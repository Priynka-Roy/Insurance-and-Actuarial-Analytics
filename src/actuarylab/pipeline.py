"""Offline real-data analysis. Public artifacts contain aggregates, never policy IDs."""
from __future__ import annotations

import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from scipy.stats import gamma as gamma_distribution
from scipy.stats import lognorm
from sklearn.linear_model import GammaRegressor
from threadpoolctl import threadpool_limits

from actuarylab.data import load_claims, load_reconciled
from actuarylab.evaluation import decile_table, frequency_metrics, policy_bootstrap, pure_premium_metrics, segment_table, severity_metrics
from actuarylab.explainability import glm_relativities, permutation_importance
from actuarylab.features import design_frame, policy_split, preprocessor
from actuarylab.frequency import NegativeBinomialDiagnostic, fit_frequency_candidates
from actuarylab.severity import distribution_shapes, fit_severity_candidates
from actuarylab.tweedie import fit_tweedie_candidates

ROOT = Path(__file__).resolve().parents[2]


def emit(message):
    print(message, flush=True)


def summary(frame):
    e, c, a = frame.Exposure.sum(), frame.PositiveClaimNb.sum(), frame.ClaimAmount.sum()
    return {'policies': len(frame), 'exposure_years': float(e), 'claims': int(c), 'claim_amount': float(a),
        'frequency': float(c/e), 'severity': float(a/c), 'pure_premium':float(a/e),
        'claiming_policy_proportion':float((frame.PositiveClaimNb>0).mean()),
        'zero_claim_policy_proportion':float((frame.PositiveClaimNb==0).mean()),
        'currency': 'source monetary units (historical nominal amounts; no currency conversion)',
        'denominators': {'frequency':'positive payments / exposure-year', 'severity':'total positive payments / positive-payment count', 'pure_premium':'aggregate paid claims / exposure-year'},
        'exposure_quantiles': {str(q):float(frame.Exposure.quantile(q)) for q in [0,.01,.25,.5,.75,.99,1]},
        'count_distribution': [{'claims':int(k), 'policies':int(v)} for k,v in frame.PositiveClaimNb.value_counts().sort_index().items()]}


def synthetic_profiles(train):
    modes = {c: train[c].mode().iloc[0] for c in ['VehPower','VehBrand','VehGas','Area','Region']}
    rows=[]
    presets = [('Experienced, low bonus-malus',45,5,50,500),('Younger, higher bonus-malus',22,2,100,2500),
        ('Mature, urban',58,3,60,10000),('Mature, rural',58,3,60,50),
        ('Older vehicle',40,15,70,1000),('Newer vehicle',40,1,70,1000),
        ('Higher bonus-malus',40,5,120,1000),('Low-density reference',40,5,70,100)]
    for name, age, vehicle_age, bm, density in presets:
        rows.append({'name':name, 'DrivAge':age, 'VehAge':vehicle_age,'BonusMalus':bm,'Density':density, **modes})
    return pd.DataFrame(rows)


def run():
    with threadpool_limits(limits=2):
        return _run()


def _run():
    started=time.time()
    protocol_path=ROOT/'configs/protocol.json'
    protocol=json.loads(protocol_path.read_text())
    protocol['sha256']=hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    emit('Loading official raw data and reconciling without payment clipping.')
    full,audit=load_reconciled()
    df=full.loc[full.Eligible].copy()
    df['split']=policy_split(df.IDpol)
    partitions={s:df.loc[df.split==s].copy() for s in ['train','validation','test']}
    claims=load_claims()
    claims=claims.loc[(claims.ClaimAmount>0)&claims.IDpol.isin(df.IDpol)].merge(df.drop(columns='ClaimAmount'),on='IDpol',validate='many_to_one')
    claim_parts={s:claims.loc[claims.split==s].copy() for s in partitions}
    train,valid,test=(partitions[s] for s in partitions)
    ct,cv,cs=(claim_parts[s] for s in partitions)
    split_report={s:{**summary(v),'identity_sha256': hashlib.sha256(','.join(map(str, sorted(v.IDpol.astype(int)))).encode()).hexdigest(),
        'positive_claim_rows':len(claim_parts[s])} for s,v in partitions.items()}
    emit(f'Split sizes: { {s:len(v) for s,v in partitions.items()} }; claims { {s:len(v) for s,v in claim_parts.items()} }')
    transform=preprocessor()
    tree_transform=preprocessor(tree=True)
    x_train=transform.fit_transform(design_frame(train))
    xt_train=tree_transform.fit_transform(design_frame(train))
    x_valid=transform.transform(design_frame(valid))
    xt_valid=tree_transform.transform(design_frame(valid))
    xc_train=transform.transform(design_frame(ct))
    xc_valid=transform.transform(design_frame(cv))
    emit(f'Fitting frequency candidates on all {len(train):,} training policies ({x_train.shape[1]} features).')
    freq=fit_frequency_candidates(x_train,train.PositiveClaimNb.to_numpy(),train.Exposure.to_numpy(),xt_train)
    baseline_f=float(train.PositiveClaimNb.sum()/train.Exposure.sum())
    valid_f={'Intercept-only Poisson':np.full(len(valid),baseline_f)}
    for name,(model,tree) in freq.items():
        valid_f[name]=model.predict(xt_valid if tree else x_valid)
    glm=freq['Poisson GLM'][0]
    expected_train=train.Exposure.to_numpy()*glm.predict(x_train)
    count=train.PositiveClaimNb.to_numpy()
    pearson=float(np.sum((count-expected_train)**2/expected_train)/(len(train)-x_train.shape[1]-1))
    alpha_nb=float(max(0,np.sum((count-expected_train)**2-expected_train)/np.sum(expected_train**2)))
    nb_diagnostic={'training_pearson_dispersion':pearson,'training_nb2_moment_alpha':alpha_nb,
        'method':'NB2 alpha=max(sum((y-mu)^2-mu)/sum(mu^2),0), based on unpenalized Poisson training fitted count means; no test outcomes used.'}
    if pearson>1.2 and alpha_nb>0:
        emit(f'Material training overdispersion {pearson:.3f}; fitting fixed-alpha NB2 development diagnostic.')
        nb=NegativeBinomialDiagnostic(alpha_nb).fit(x_train,count,train.Exposure.to_numpy(),np.r_[glm.intercept_,glm.coef_])
        nb_diagnostic.update({'converged':nb.converged_,'optimization_message':nb.optimization_message_})
        if nb.converged_:
            freq['NB2 moment-dispersion GLM']=(nb,False)
            valid_f['NB2 moment-dispersion GLM']=nb.predict(x_valid)
    freq_scores={k:frequency_metrics(valid.PositiveClaimNb,valid.Exposure,v,baseline_f) for k,v in valid_f.items()}
    freq_choice=min(freq_scores,key=lambda k:freq_scores[k]['poisson_deviance_per_exposure'])
    emit('Fitting individual positive-payment Gamma severity candidates; all large claims retained.')
    sev=fit_severity_candidates(xc_train,ct.ClaimAmount.to_numpy())
    baseline_s=float(ct.ClaimAmount.mean())
    valid_s={'Intercept-only Gamma':np.full(len(cv),baseline_s)}
    valid_s.update({k:m.predict(xc_valid) for k,m in sev.items()})
    sev_scores={k:severity_metrics(cv.ClaimAmount,v) for k,v in valid_s.items()}
    sev_choice=min(sev_scores,key=lambda k:sev_scores[k]['gamma_deviance'])
    def predict_frequency(name, frame, x=None, xt=None):
        if name=='Intercept-only Poisson':
            return np.full(len(frame),baseline_f)
        m,tree=freq[name]
        xx=(tree_transform if tree else transform).transform(design_frame(frame)) if x is None else (xt if tree else x)
        return m.predict(xx)
    def predict_severity(name,frame,x=None):
        if name=='Intercept-only Gamma':
            return np.full(len(frame),baseline_s)
        return sev[name].predict(transform.transform(design_frame(frame)) if x is None else x)
    emit('Fitting six direct Tweedie candidates; comparing all premiums at common p=1.5.')
    tweedie=fit_tweedie_candidates(x_train,train.ClaimAmount.to_numpy(),train.Exposure.to_numpy())
    valid_p={'Two-part frequency × severity':valid_f[freq_choice]*predict_severity(sev_choice,valid,x_valid)}
    valid_p.update({k:m.predict(x_valid) for k,m in tweedie.items()})
    pp_scores={k:pure_premium_metrics(valid.ClaimAmount,valid.Exposure,v) for k,v in valid_p.items()}
    pp_choice=min(pp_scores,key=lambda k:pp_scores[k]['tweedie_deviance_p1_5'])
    selected_direct=min(tweedie,key=lambda k:pp_scores[k]['tweedie_deviance_p1_5'])
    selection={'frequency':freq_choice,'severity':sev_choice,'pure_premium':pp_choice,'direct_tweedie':selected_direct,
        'criterion':protocol['selection'],'refit':False,'test_used_for_selection':False,
        'frozen_protocol_sha256':protocol['sha256']}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/selection_frozen.json').write_text(json.dumps(selection,indent=2)+'\n')
    emit(f'FROZEN before test: {selection}')
    # Every target/hyperparameter decision above depends on development only.
    x_test=transform.transform(design_frame(test))
    xt_test=tree_transform.transform(design_frame(test))
    xc_test=transform.transform(design_frame(cs))
    test_f={k:predict_frequency(k,test,x_test,xt_test) for k in valid_f}
    test_s={k:predict_severity(k,cs,xc_test) for k in valid_s}
    test_sev_policy=predict_severity(sev_choice,test,x_test)
    test_p={'Two-part frequency × severity':test_f[freq_choice]*test_sev_policy}
    test_p.update({k:m.predict(x_test) for k,m in tweedie.items()})
    model_tables={
        'frequency':[{'model':k,'selected':k==freq_choice,'validation':freq_scores[k],
            'test':frequency_metrics(test.PositiveClaimNb,test.Exposure,v,baseline_f)} for k,v in test_f.items()],
        'severity':[{'model':k,'selected':k==sev_choice,'validation':sev_scores[k],
            'test':severity_metrics(cs.ClaimAmount,v)} for k,v in test_s.items()],
        'pure_premium':[{'model':k,'selected':k==pp_choice,'validation':pp_scores[k],
            'test':pure_premium_metrics(test.ClaimAmount,test.Exposure,v)} for k,v in test_p.items()]}
    chosen_f,chosen_p=test_f[freq_choice],test_p[pp_choice]
    claim_predictions=predict_severity(sev_choice,cs,xc_test)
    test_severity_total=test.PositiveClaimNb.to_numpy()*test_sev_policy
    alternative_freq=min([k for k in freq if 'Poisson GLM' in k],key=lambda k:freq_scores[k]['poisson_deviance_per_exposure'])
    ml_freq=min([k for k in freq if 'HGB' in k],key=lambda k:freq_scores[k]['poisson_deviance_per_exposure'])
    emit('Computing 250 policy-cluster bootstrap draws and fixed-model validation diagnostics.')
    uncertainty=policy_bootstrap(test,{ml_freq:test_f[ml_freq],alternative_freq:test_f[alternative_freq]},
        {selected_direct:test_p[selected_direct],'Two-part frequency × severity':test_p['Two-part frequency × severity']},
        test_severity_total)
    # O/E intervals must describe selected model, not arbitrary comparator ordering.
    claim_gamma_unit=2*((cs.ClaimAmount.to_numpy()-claim_predictions)/claim_predictions - np.log(cs.ClaimAmount.to_numpy()/claim_predictions))
    policy_gamma=pd.Series(claim_gamma_unit,index=cs.IDpol).groupby(level=0).sum()
    policy_gamma_sums=test.IDpol.map(policy_gamma).fillna(0).to_numpy()
    selected_intervals=policy_bootstrap(test,{freq_choice:chosen_f},{pp_choice:chosen_p},test_severity_total,
        severity_deviance_sums=policy_gamma_sums)
    uncertainty['intervals']=selected_intervals['intervals']
    uncertainty['interval_model']={'frequency':freq_choice,'severity':sev_choice,'premium':pp_choice}
    gamma_shape_info=distribution_shapes(ct.ClaimAmount,predict_severity(sev_choice,ct,xc_train))
    threshold=float(ct.ClaimAmount.quantile(.99))
    capped=GammaRegressor(alpha=.1,max_iter=500,tol=1e-7).fit(xc_train,np.minimum(ct.ClaimAmount,threshold))
    cap_pred=capped.predict(xc_valid)
    full_pred=predict_severity(sev_choice,cv,xc_valid)
    large_sensitivity={'training_p99_threshold':threshold,'training_claims_above_threshold':int((ct.ClaimAmount>threshold).sum()),
        'training_amount_share_above_threshold':float(ct.loc[ct.ClaimAmount>threshold,'ClaimAmount'].sum()/ct.ClaimAmount.sum()),
        'method':'Diagnostic Gamma alpha=.1 refit using training payment cap at training99percentile; validation-only assessment. Primary selection and all main scores remain uncapped.',
        'capped_model_validation_full_cost':severity_metrics(cv.ClaimAmount,cap_pred),
        'capped_model_validation_capped_cost':severity_metrics(np.minimum(cv.ClaimAmount,threshold),cap_pred),
        'primary_validation_full_cost':severity_metrics(cv.ClaimAmount,full_pred)}
    e=test.Exposure.to_numpy()
    mu=chosen_f*e
    zero_observed=float((test.PositiveClaimNb==0).mean())
    residuals={'training_poisson_glm':nb_diagnostic,
        'test_selected_pearson_dispersion':float(np.mean((test.PositiveClaimNb.to_numpy()-mu)**2/mu)),
        'observed_zero_proportion':zero_observed,'poisson_implied_zero_proportion':float(np.mean(np.exp(-mu))),
        'test_selected_count_mean':float(test.PositiveClaimNb.mean()),'test_selected_count_variance':float(test.PositiveClaimNb.var()),
        'caution':'Unconditional count variance also reflects exposure and risk heterogeneity. Zero mismatch alone does not establish zero inflation.'}
    quantiles=[.5,.9,.95,.99,.999]
    relative_train=ct.ClaimAmount.to_numpy()/predict_severity(sev_choice,ct,xc_train)
    tail_table=[{'quantile':q,'observed_training_relative_payment':float(np.quantile(relative_train,q)),
        'gamma_assumed_relative_payment':float(gamma_distribution.ppf(q,a=gamma_shape_info['gamma_shape'],scale=1/gamma_shape_info['gamma_shape'])),
        'lognormal_assumed_relative_payment':float(lognorm.ppf(q,s=gamma_shape_info['lognormal_sigma'],scale=np.exp(-.5*gamma_shape_info['lognormal_sigma']**2)))} for q in quantiles]
    emit('Computing development-only permutation importance and synthetic profile predictions.')
    importance_model=freq[ml_freq][0]
    importance=permutation_importance(valid,importance_model,tree_transform)
    profiles_df=synthetic_profiles(train)
    xf=transform.transform(design_frame(profiles_df))
    xtf=tree_transform.transform(design_frame(profiles_df))
    pf=predict_frequency(freq_choice,profiles_df,xf,xtf)
    ps=predict_severity(sev_choice,profiles_df,xf)
    pdirect=tweedie[selected_direct].predict(xf)
    profiles=[]
    for idx,row in profiles_df.iterrows():
        features={k:(v.item() if isinstance(v,np.generic) else v) for k,v in row.drop('name').items()}
        profiles.append({'name':row['name'],'features':features,'frequency':float(pf[idx]),'severity':float(ps[idx]),
            'two_part_pure_premium':float(pf[idx]*ps[idx]),'direct_tweedie_pure_premium':float(pdirect[idx]),
            'selected_pure_premium':float((pf*ps if pp_choice=='Two-part frequency × severity' else pdirect)[idx]),
            'exposure':1.,'expected_policy_cost':float((pf*ps if pp_choice=='Two-part frequency × severity' else pdirect)[idx]),
            'warning':'Invented illustrative profile, not an identifiable source policy or insurance offer.'})
    cells=[{'frequency':r['frequency'],'severity':r['severity'],'exposure':1.,'weight':1/len(profiles),'name':r['name']} for r in profiles]
    claim_hist_edges=[0,500,1000,2000,5000,10000,25000,100000,1e6,float(claims.ClaimAmount.max())+1]
    claim_hist=np.histogram(claims.ClaimAmount,bins=claim_hist_edges)[0]
    charts={'claim_amount_histogram':[{'lower':float(a),'upper':float(b),'claims':int(n)} for a,b,n in zip(claim_hist_edges[:-1],claim_hist_edges[1:],claim_hist,strict=True)],
        'exposure_histogram':[{'lower':float(a),'upper':float(b),'policies':int(n)} for a,b,n in zip([0,.1,.25,.5,.75,1], [.1,.25,.5,.75,1,float(df.Exposure.max())+.001], np.histogram(df.Exposure,bins=[0,.1,.25,.5,.75,1,float(df.Exposure.max())+.001])[0],strict=True)]}
    segments={k:segment_table(test,chosen_f,test_sev_policy,chosen_p,k) for k in ['DrivAge','VehAge','Region','VehGas','Area']}
    diagnostic_cohort=full.loc[full.Exposure.gt(0)&full.ClaimNb.ge(0)&full.ClaimNb.notna()]
    alternative_reconciliation={'development_only':True,'primary_definition':'Count-consistent known-payment cohort; missing payments excluded, not treated as zero.',
        'all_clean_frequency_development':summary_count_only(diagnostic_cohort.loc[policy_split(diagnostic_cohort.IDpol)!='test']),
        'primary_development':summary_count_only(pd.concat([train,valid])),
        'warning':'Different populations and claim definitions; this descriptive comparison does not estimate missing payment amounts or validate discarding them.'}
    severity_deciles=decile_table(cs.ClaimAmount,np.ones(len(cs)),claim_predictions,'amount')
    for row in severity_deciles:
        row['claims']=row.pop('policies')
        row['claim_weight']=row.pop('exposure')
        row['denominator']='positive individual payments (unit claim weights), not policy exposure-years'
        row['cohort']='Positive-payment claims from final holdout policies; all claims inherit their parent policy split.'
    validation={'split_summary':split_report,'frequency_deciles':decile_table(test.PositiveClaimNb,e,chosen_f,'claims'),
        'premium_deciles':decile_table(test.ClaimAmount,e,chosen_p,'loss'),
        'severity_deciles':severity_deciles,
        'holdout_design':'One frozen policy-level random holdout, not out-of-time or prospective validation.',
        'concentration_definition':'1 - 2 integral(cumulative observed loss share against cumulative exposure share), ordered increasing selected premium prediction; exposure concentration index, not causal discrimination or normalized Gini.'}
    diagnostics={'frequency_residuals':residuals,'large_claim_sensitivity':large_sensitivity,
        'severity_distribution':gamma_shape_info,'tail_fit_diagnostic':tail_table,
        'reconciliation_sensitivity':alternative_reconciliation,'charts':charts,
        'primary_data_scope':'All EDA claims/costs/model metrics refer to strict reconciled economic cohort unless source audit is explicitly named.'}
    explanation={'frequency_glm_relativities':glm_relativities(glm,transform),
        'severity_glm_relativities':glm_relativities(sev.get(sev_choice,sev['Gamma GLM']),transform),
        'severity_relativity_model':sev_choice if sev_choice in sev else 'Gamma GLM (diagnostic comparator; selected severity is intercept)',
        'ml_frequency_permutation':importance,'permutation_model':ml_freq,
        'reference_categories':{c:str(cats[0]) for c,cats in zip(['VehPower','VehBrand','VehGas','Area','Region'],transform.named_transformers_['categorical'][-1].categories_,strict=True)},
        'warning':'Conditional model associations and permutation effects, not causal effects or approved rating factors.'}
    artifact={'schema_version':'1.0.0','summary':summary(df),'audit':audit,'models':model_tables,'selection':selection,
        'validation':validation,'uncertainty':uncertainty,'segments':segments,'diagnostics':diagnostics,
        'explainability':explanation,'profiles':profiles,'simulation_inputs':{'cells':cells,**gamma_shape_info,
            'portfolio_definition':'Equal-weight mixture of eight synthetic one-year profiles; not a reconstruction of source records; uses selected two-part components even if direct Tweedie wins pricing selection.'},
        'case_studies':cases(model_tables,selection,uncertainty,profiles,residuals,large_sensitivity),
        'protocol':protocol,'limitations':[
            'Historical French MTPL sample; no reliable prospective or out-of-time validation; not current Nordic insurance experience.',
            'Strict count-payment reconciliation excludes unresolved histories and can change selection/population composition.',
            'Payment development, inflation, recoveries, deductibles, limits and missing payment histories are not fully known.',
            'Large losses are retained; a small number dominate severity, calibration, uncertainty and simulated tails.',
            'Pointwise bootstrap intervals condition on fitted models and ignore model-selection uncertainty.',
            'Gamma/lognormal and Poisson risk assumptions are illustrative; model mean scores do not validate tail distributions.',
            'Predictive demographic/geographic associations are not causal or evidence of pricing permissibility.',
            'No insurer endorsement, underwriting approval, regulatory certification or production pricing claim.'],
        'reproducibility':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scikit_learn':sklearn.__version__,
            'elapsed_seconds':round(time.time()-started,2),'cross_platform':'Floating-point results may vary by BLAS/platform; exact bitwise cross-platform reproducibility not claimed.'}}
    for destination in ['reports/results.json','artifacts/dashboard.json']:
        path=ROOT/destination
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(artifact,indent=2,allow_nan=False)+'\n')
    emit(f'Exported real-data aggregate artifact in {time.time()-started:.1f}s.')
    return artifact


def summary_count_only(frame):
    return {'policies':len(frame),'exposure':float(frame.Exposure.sum()),'source_claims':int(frame.ClaimNb.sum()),
            'source_claim_frequency':float(frame.ClaimNb.sum()/frame.Exposure.sum())}


def cases(tables,selection,uncertainty,profiles,residuals,sensitivity):
    def selected(task):
        return next(r for r in tables[task] if r['selected'])['test']
    f,s,p=selected('frequency'),selected('severity'),selected('pure_premium')
    return [
        {'id':'A','title':'Why exposure adjustment matters','question':'How do annual rates differ from claim probability?',
         'method':'Annual rate is positive-payment count divided by exposure; fitted count = exposure × annual rate.',
         'result':f"Holdout observed rate {f['observed_rate']:.6f} payments per exposure-year; selected predicted rate {f['predicted_rate']:.6f}.",
         'limitation':'Claim frequency permits multiple claims; it is not the proportion of policies with a claim.'},
        {'id':'B','title':'Poisson versus nonlinear and NB2 frequency','question':'Does a more flexible mean improve exposure-aware scores?',
         'method':'All candidates use positive-payment annual-frequency target and exposure weights; validation deviance selects once.',
         'result':f"Selected {selection['frequency']}; holdout Poisson deviance/exposure {f['poisson_deviance_per_exposure']:.6f}. Training Pearson dispersion {residuals['training_poisson_glm']['training_pearson_dispersion']:.3f}.",
         'limitation':'Poisson scoring evaluates conditional means; this does not prove the full count distribution is Poisson.'},
        {'id':'C','title':'Gamma severity and large claims','question':'How sensitive is severity to the right tail?',
         'method':'Individual positive payments inherit policy split; primary scores use every uncapped claim. A capped refit is a development-only diagnostic.',
         'result':f"Selected {selection['severity']}; holdout Gamma deviance {s['gamma_deviance']:.6f}. Above-training-p99 payments contribute {sensitivity['training_amount_share_above_threshold']:.1%} of training paid cost.",
         'limitation':'Good mean deviance does not validate Gamma extreme-tail behavior.'},
        {'id':'D','title':'Two-part pricing versus direct Tweedie','question':'Which approach scores better on the frozen common criterion?',
         'method':'Compare all models with exposure-weighted Tweedie deviance at fixed p=1.5, including models trained with p=1.3/1.7.',
         'result':f"Selected {selection['pure_premium']}; holdout common-p deviance {p['tweedie_deviance_p1_5']:.4f}, observed/expected loss {p['observed_expected_ratio']:.4f}.",
         'limitation':'Direct Tweedie does not independently identify frequency and severity components; selected on validation only.'},
        {'id':'E','title':'Validation and policy-cluster uncertainty','question':'How uncertain are observed rates and calibration?',
         'method':uncertainty['method'],
         'result':f"Holdout pure-premium percentile interval [{uncertainty['intervals']['pure_premium']['lower']:.2f}, {uncertainty['intervals']['pure_premium']['upper']:.2f}] source units/exposure-year.",
         'limitation':uncertainty['warning']},
        {'id':'F','title':'How portfolio composition changes mean cost','question':'How do synthetic profiles contribute different expected losses?',
         'method':'Invented covariate profiles pass through the fixed training-fitted models; they are not identifiable source policies.',
         'result':f"Across eight illustrative one-year profiles, selected annual pure premium ranges {min(r['selected_pure_premium'] for r in profiles):.2f}–{max(r['selected_pure_premium'] for r in profiles):.2f} source units.",
         'limitation':'Associations do not establish causal effects, allowed rating factors or real offers.'}
    ]
