from fastapi import APIRouter, HTTPException, status, Depends
from models.salary_model import SalaryInput
from utilities.calculator_funtions import  calculate_isr, calculare_imss
from controllers.user_controller import get_current_user, TokenData
router = APIRouter()


@router.post("/finance/calculator")
async def get_calculator(salary_input: SalaryInput, current_user: TokenData = Depends(get_current_user))->dict[str, float]:
    try:

        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        isr = calculate_isr(salary_input.gross_salary, salary_input.period)
        imss = calculare_imss(salary_input.gross_salary, salary_input.period) if salary_input.include_imss else 0

        net_salary = salary_input.gross_salary - isr - imss
        return {
            "net_salary": net_salary,
            "taxes": isr,
            "imss": imss,
        }
    except HTTPException as http_e:

        raise http_e

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

