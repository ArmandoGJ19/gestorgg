from fastapi import HTTPException

weekly_brackets = [
    {"lower": 0.01, "upper": 171.78, "fixedFee": 0.00, "rate": 1.92},
    {"lower": 171.79, "upper": 1458.03, "fixedFee": 3.29, "rate": 6.40},
    {"lower": 1458.04, "upper": 2562.35, "fixedFee": 85.61, "rate": 10.88},
    {"lower": 2562.36, "upper": 2978.64, "fixedFee": 205.80, "rate": 16.00},
    {"lower": 2978.65, "upper": 3566.22, "fixedFee": 272.37, "rate": 17.92},
    {"lower": 3566.23, "upper": 7192.64, "fixedFee": 377.65, "rate": 21.36},
    {"lower": 7192.65, "upper": 11336.57, "fixedFee": 1152.27, "rate": 23.52},
    {"lower": 11336.58, "upper": 21643.30, "fixedFee": 2126.95, "rate": 30.00},
    {"lower": 21643.31, "upper": 28857.78, "fixedFee": 5218.92, "rate": 32.00},
    {"lower": 28857.79, "upper": 86573.34, "fixedFee": 7527.59, "rate": 34.00},
    {"lower": 86573.35, "upper": float("inf"), "fixedFee": 27150.83, "rate": 35.00},
]
biweekly_brackets = [
    {"lower": 0.01, "upper": 368.10, "fixedFee": 0.00, "rate": 1.92},
    {"lower": 368.11, "upper": 3124.35, "fixedFee": 7.05, "rate": 6.40},
    {"lower": 3124.36, "upper": 5490.75, "fixedFee": 183.45, "rate": 10.88},
    {"lower": 5490.76, "upper": 6382.80, "fixedFee": 441.00, "rate": 16.00},
    {"lower": 6382.81, "upper": 7641.90, "fixedFee": 583.65, "rate": 17.92},
    {"lower": 7641.91, "upper": 15412.80, "fixedFee": 809.25, "rate": 21.36},
    {"lower": 15412.81, "upper": 24292.65, "fixedFee": 2469.15, "rate": 23.52},
    {"lower": 24292.66, "upper": 46378.10, "fixedFee": 4557.75, "rate": 30.00},
    {"lower": 46378.51, "upper": 61838.10, "fixedFee": 11183.40, "rate": 32.00},
    {"lower": 61838.11, "upper": 185514.30, "fixedFee": 16130.55, "rate": 34.00},
    {"lower": 185514.31, "upper": float("inf"), "fixedFee": 58180.35, "rate": 35.00}
]
monthly_brackets = [
    {"lower": 0.01, "upper": 746.04, "fixedFee": 0.00, "rate": 1.92},
    {"lower": 746.05, "upper": 6332.05, "fixedFee": 14.32, "rate": 6.40},
    {"lower": 6332.06, "upper": 11228.01, "fixedFee": 371.83, "rate": 10.88},
    {"lower": 11228.02, "upper": 12935.82, "fixedFee": 893.63, "rate": 16.00},
    {"lower": 12935.83, "upper": 15487.71, "fixedFee": 1182.88, "rate": 17.92},
    {"lower": 15487.72, "upper": 31236.49, "fixedFee": 1640.18, "rate": 21.36},
    {"lower": 31236.50, "upper": 49233.00, "fixedFee": 5004.12, "rate": 23.52},
    {"lower": 49233.01, "upper": 93993.90, "fixedFee": 9236.89, "rate": 30.00},
    {"lower": 93993.91, "upper": 125325.20, "fixedFee": 22665.17, "rate": 32.00},
    {"lower": 125325.21, "upper": 375975.61, "fixedFee": 32691.18, "rate": 34.00},
    {"lower": 375975.62, "upper": float("inf"), "fixedFee": 117912.32, "rate": 35.00}
]


def calculate_isr(gross_salary: float, period: str):
    if period == "weekly":
        brackets = weekly_brackets
    elif period == "biweekly":
        brackets = biweekly_brackets
    else:
        brackets = monthly_brackets
    applicable_bracket = next((bracket for bracket in brackets if bracket["lower"] < gross_salary <= bracket["upper"]),
                              None)
    if applicable_bracket:
        isr = applicable_bracket["fixedFee"] + (
                    (gross_salary - applicable_bracket["lower"]) * applicable_bracket["rate"]) / 100
        return isr
    else:
        raise HTTPException(status_code=400, detail="Invalid salary or period")


def calculare_imss(gross_salary: float, period: str):
    days_in_period = 0
    if period == "weekly":
        days_in_period = 7
    elif period == "biweekly":
        days_in_period = 14
    else:
        days_in_period = 30

    daily_salary = gross_salary / days_in_period
    uma = 108.74
    uma_monthly = uma * 30.4
    max_sbc = uma * 25

    sbc_per = min(daily_salary, max_sbc)

    enfermedad_maternidad_inero = 0.25
    pensionados_beneficiarios = 0.375
    invalidez_vida = 0.625
    cesantia_vejez = 1.125

    deducciones_empleo = sbc_per * days_in_period * (
                enfermedad_maternidad_inero + pensionados_beneficiarios + invalidez_vida + cesantia_vejez) / 100

    exedente_salud = 0
    if sbc_per * days_in_period > uma_monthly * 3:
        exedente = sbc_per * days_in_period - uma_monthly * 3
        exedente_salud = exedente * 0.45 / 100

    deducciones_empleo += exedente_salud

    return deducciones_empleo


# def calculate_subsidy(gross_salary: float) -> float:
#     subsidy = 0
#     if gross_salary <= 30000:
#         subsidy = 500
#     return subsidy

