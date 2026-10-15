"""Illustrative expense/profit shares of final premium, not insurer tariffs."""
import math


def quote(pure_premium, exposure=1.0, expense=0.20, risk=0.05, profit=0.05, fixed=0.0):
    values = [pure_premium, exposure, expense, risk, profit, fixed]
    if any(not math.isfinite(float(x)) or x < 0 for x in values):
        raise ValueError('Pricing assumptions must be finite and nonnegative.')
    if expense + profit >= 1 or expense > 0.8 or profit > 0.8 or risk > 3 or exposure > 5:
        raise ValueError('Invalid loading shares or exposure outside illustrative bounds.')
    annual = (pure_premium * (1 + risk) + fixed) / (1 - expense - profit)
    expected = pure_premium * exposure
    premium = annual * exposure
    return {'pure_premium': float(pure_premium), 'annual_premium': float(annual),
            'policy_expected_loss': float(expected), 'policy_premium': float(premium),
            'expected_loss_ratio': float(expected / premium) if premium > 0 else None,
            'expense_share': float(expense), 'profit_share': float(profit),
            'risk_loading': float(risk), 'exposure': float(exposure), 'fixed_annual_cost': float(fixed),
            'formula': '(pure premium × (1 + risk loading) + fixed annual cost) / (1 − expense share − profit share)'}
