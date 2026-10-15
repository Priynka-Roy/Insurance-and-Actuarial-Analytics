"""Append bounded hypothetical simulations/pricing and seal aggregate artifacts."""
from pathlib import Path
import sys
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from actuarylab.pricing import quote  # noqa: E402
from actuarylab.simulation import simulate_portfolio  # noqa: E402


def export():
    result = json.loads((ROOT / 'reports/results.json').read_text())
    inputs = result['simulation_inputs']
    cells = inputs['cells']
    frequency = np.array([row['frequency'] for row in cells])
    severity = np.array([row['severity'] for row in cells])
    weights = np.array([row['weight'] for row in cells])
    exposure = np.array([row['exposure'] for row in cells]) * weights / weights.sum() * 1000
    expected = float(np.dot(frequency * exposure, severity))
    baseline_quote = quote(expected / exposure.sum(), exposure=1)
    premium = baseline_quote['annual_premium'] * exposure.sum()
    definitions = [
        ('Baseline · independent Gamma', {}),
        ('Frequency +20%', {'frequency_multiplier': 1.2}),
        ('Severity +20%', {'severity_multiplier': 1.2}),
        ('Combined +20% frequency and severity', {'frequency_multiplier':1.2,'severity_multiplier':1.2}),
        ('Alternative lognormal severity · same means', {'tail':'lognormal'}),
        ('Shared frequency shock · mean preserved', {'common_sigma':.35}),
    ]
    scenarios = []
    for name, changes in definitions:
        sim = simulate_portfolio(frequency,severity,exposure,replicates=10000,seed=442,
                                 gamma_shape=inputs['gamma_shape'],lognormal_sigma=inputs['lognormal_sigma'],
                                 premium=premium,**changes)
        sim.update({'name': name, 'pure_premium': sim['expected_loss'] / sim['portfolio_exposure'],
                    'plot_sample_size': 1000, 'plot_sample_note':'Display uses the first 1,000 of 10,000 simulations; risk summaries use all 10,000.'})
        sim['losses'] = sim['losses'][:1000]
        scenarios.append(sim)
    mix = np.full(len(cells), .5 / (len(cells) - 1))
    mix[1] = .5
    sim = simulate_portfolio(frequency,severity,mix*1000,replicates=10000,seed=442,
                             gamma_shape=inputs['gamma_shape'],lognormal_sigma=inputs['lognormal_sigma'],premium=premium)
    sim.update({'name':'Portfolio mix · younger profile weight 50%', 'pure_premium':sim['expected_loss']/1000,
                'plot_sample_size':1000,'plot_sample_note':'Display uses the first 1,000 of 10,000 simulations; risk summaries use all 10,000.',
                'mix_weights':mix.tolist()})
    sim['losses'] = sim['losses'][:1000]
    scenarios.append(sim)
    result['pricing'] = {'baseline_quote':baseline_quote,'assumed_portfolio_premium':premium,
                         'portfolio_exposure':float(exposure.sum()),'note':'Illustrative expense share20%, profit share5%, risk loading5%, fixed cost0; premium held fixed across stress scenarios. No observed insurer premium or profit data.',
                         'profiles':[{'name':p['name'],**quote(p['selected_pure_premium'])} for p in result['profiles']]}
    result['simulation'] = {'scenarios':scenarios,'portfolio_size':1000,'replicates':10000,
                            'portfolio_definition':inputs['portfolio_definition'],
                            'assumptions':['Synthetic equal-weight mixture of eight fitted profiles, 125 one-year policies of each type; composition scenario explicitly changes weights.',
                                           'Poisson count means from selected frequency; Gamma/lognormal claim means from selected positive severity.',
                                           'Gamma shape and lognormal log-residual scale estimated on training only; both severity alternatives normalized to the same conditional means.',
                                           'Baseline conditional independence. Shared count-rate factor exp(sigma Z − sigma²/2) has mean one, preserves marginal expected loss and adds process variability; sigma0.35 is hypothetical.',
                                           'All stresses and commercial premium loadings are hypothetical. SMU are source monetary units; no FX or inflation conversion.',
                                           'Monte Carlo standard error is sample loss SD/sqrt(R). It describes numerical mean precision, not model parameter uncertainty or reliable tail-quantile precision.',
                                           'VaR uses inverse empirical CDF; ES averages exact worst-tail probability mass with fractional boundary/tie handling. No Solvency II/regulatory capital claim.'],
                            'tail_warning':'Mean models do not validate severity tail distributions. Only 100 simulated portfolios lie in the 99% tail; estimates can be unstable and omit catastrophe, development, inflation and parameter uncertainty.'}
    baseline, freq_stress, sev_stress, combined, lognormal, shock = scenarios[:6]
    result['case_studies'] = [c for c in result['case_studies'] if c['id'] not in ['G','H']] + [
        {'id':'G','title':'Monte Carlo aggregate loss and tail assumptions',
         'question':'How does the assumed severity tail change simulated portfolio risk?',
         'method':'10,000 aggregate simulations for 1,000 synthetic one-year policies; Gamma versus lognormal severity, matching fitted conditional means.',
         'result':f"Shared analytical expected loss {expected:,.2f} SMU. Gamma ES95 {baseline['es95']:,.2f}; lognormal ES95 {lognormal['es95']:,.2f}. Mean-preserving shared frequency shock ES95 {shock['es95']:,.2f}.",
         'interpretation':'Different distributional assumptions can materially change extreme-loss estimates even when expected losses agree.',
         'limitation':'Hypothetical synthetic composition; fitted mean diagnostics do not establish a valid extreme tail. Monte Carlo and parameter uncertainties are different.'},
        {'id':'H','title':'Premium adequacy under hypothetical stress',
         'question':'What happens when incidence and payment severity both rise while assumed premium stays fixed?',
         'method':'Raise each component by20%; expected loss increases multiplicatively by1.44. Keep illustrative portfolio premium fixed.',
         'result':f"Baseline expected loss ratio {baseline['expected_loss_ratio']:.2%}; frequency-only {freq_stress['expected_loss_ratio']:.2%}; severity-only {sev_stress['expected_loss_ratio']:.2%}; combined {combined['expected_loss_ratio']:.2%}.",
         'interpretation':'An assumed premium cushion can be exhausted by compound stress; this is expected loss divided by hypothetical premium, not observed insurer profitability.',
         'limitation':'No actual earned premiums, expenses, tax or profit observations. Stress sizes are assumptions rather than economic forecasts.'}]
    for name in ['reports/results.json','artifacts/dashboard.json']:
        (ROOT/name).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    required = ['artifacts/dashboard.json','reports/results.json','configs/protocol.json','reports/data_provenance.json','reports/reconciliation.json','reports/selection_frozen.json']
    manifest = {'schema_version':1,'files':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in required}}
    (ROOT/'artifacts/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps([{k:s[k] for k in ['name','expected_loss','mean','mean_se','mean_error_in_se','var95','es95','var99','es99','expected_loss_ratio']} for s in scenarios],indent=2))


if __name__ == '__main__':
    export()
