from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from app.extensions import db
from app.models.budget import Budget
from app.models.purchase import Purchase
from app.forms.budget_forms import BudgetForm
from app.forms.purchase_forms import UndoPurchaseForm

budget_bp = Blueprint("budget", __name__, url_prefix="/budget")


@budget_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """
    Budget Manager:
    - Set/Update monthly shopping budget
    - View total spending for the selected month
    - View remaining budget & spending percentage
    - Trigger 80% warning and budget exceeded alert
    - View monthly purchases and spending breakdown
    """
    user_id = current_user.id
    today = date.today()

    # Allow querying different months (defaults to current month and year)
    selected_year = request.args.get("year", default=today.year, type=int)
    selected_month = request.args.get("month", default=today.month, type=int)

    # Sanity checks on month/year
    if selected_month < 1 or selected_month > 12:
        selected_month = today.month
    if selected_year < 2020 or selected_year > 2100:
        selected_year = today.year

    form = BudgetForm()

    # Handle Budget Update/Creation
    if form.validate_on_submit():
        target_year = form.year.data
        target_month = form.month.data
        new_amount = form.monthly_budget.data

        budget_record = Budget.query.filter_by(
            user_id=user_id, year=target_year, month=target_month
        ).first()

        if budget_record:
            budget_record.monthly_budget = new_amount
        else:
            budget_record = Budget(
                user_id=user_id,
                year=target_year,
                month=target_month,
                monthly_budget=new_amount,
            )
            db.session.add(budget_record)

        db.session.commit()
        flash(
            f"Budget for {date(target_year, target_month, 1).strftime('%B %Y')} set to ₹{float(new_amount):,.2f}.",
            "success",
        )
        return redirect(
            url_for("budget.index", year=target_year, month=target_month)
        )

    # Load current budget record for the selected month
    budget_record = Budget.query.filter_by(
        user_id=user_id, year=selected_year, month=selected_month
    ).first()

    monthly_budget = float(budget_record.monthly_budget) if budget_record else 0.0

    # Populate form defaults
    if request.method == "GET":
        form.year.data = selected_year
        form.month.data = selected_month
        form.monthly_budget.data = budget_record.monthly_budget if budget_record else 0.0

    # Calculate actual spending for selected month from database purchases
    month_spent_query = (
        Purchase.query.with_entities(func.sum(Purchase.actual_amount))
        .filter(
            Purchase.user_id == user_id,
            extract("year", Purchase.purchase_date) == selected_year,
            extract("month", Purchase.purchase_date) == selected_month,
        )
        .scalar()
    )
    month_spent = float(month_spent_query or 0.0)

    remaining_budget = monthly_budget - month_spent if monthly_budget > 0 else 0.0
    spent_percentage = (
        round((month_spent / monthly_budget) * 100, 1) if monthly_budget > 0 else 0.0
    )

    # Security & business rules: 80% warning and Exceeded alert
    is_budget_exceeded = monthly_budget > 0 and month_spent > monthly_budget
    is_budget_warning = (
        monthly_budget > 0
        and not is_budget_exceeded
        and spent_percentage >= 80.0
    )

    # Monthly purchase breakdown list
    monthly_purchases = (
        Purchase.query.filter(
            Purchase.user_id == user_id,
            extract("year", Purchase.purchase_date) == selected_year,
            extract("month", Purchase.purchase_date) == selected_month,
        )
        .order_by(Purchase.purchase_date.desc())
        .all()
    )

    # Monthly breakdown for the last 6 months (for chart visual)
    monthly_trends = []
    for i in range(5, -1, -1):
        # Calculate year and month offset
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        b_rec = Budget.query.filter_by(user_id=user_id, year=y, month=m).first()
        b_val = float(b_rec.monthly_budget) if b_rec else 0.0

        s_val_query = (
            Purchase.query.with_entities(func.sum(Purchase.actual_amount))
            .filter(
                Purchase.user_id == user_id,
                extract("year", Purchase.purchase_date) == y,
                extract("month", Purchase.purchase_date) == m,
            )
            .scalar()
        )
        s_val = float(s_val_query or 0.0)

        month_label = date(y, m, 1).strftime("%b %y")
        monthly_trends.append(
            {
                "label": month_label,
                "year": y,
                "month": m,
                "budget": b_val,
                "spent": s_val,
            }
        )

    undo_form = UndoPurchaseForm()

    return render_template(
        "budget/index.html",
        form=form,
        undo_form=undo_form,
        selected_year=selected_year,
        selected_month=selected_month,
        month_name=date(selected_year, selected_month, 1).strftime("%B"),
        monthly_budget=monthly_budget,
        month_spent=month_spent,
        remaining_budget=remaining_budget,
        spent_percentage=spent_percentage,
        is_budget_warning=is_budget_warning,
        is_budget_exceeded=is_budget_exceeded,
        monthly_purchases=monthly_purchases,
        monthly_trends=monthly_trends,
    )
