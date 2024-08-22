from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import CustomUser
from apps.activity.filter_expenses import ExpenseFilter
from apps.activity.forms import ExpenseEntryForm
from apps.activity.models import ExpenseEntry
from apps.activity.summary import calculate_summary_expenses
from apps.matters.models import Matter


@login_required
def list_expenses(request):
    """
    Display a list of activity expenses

    Loads an instance of Filter, which holds a list of paramaters defining
    which expenses to display.

    Calls the "calculate_summary" function to calculate totals of
    hours and fees.
    """

    expenses = ExpenseEntry.objects.all()
    number_expenses = expenses.count()

    filter_data = request.session.get("expense_filter", None)

    if filter_data:
        filter = ExpenseFilter(filter_data)
        expenses = filter.qs

        order = filter_data.get("order", "date, ascending")
        if order == "date, descending":
            expenses.order_by("-date", "-id")
        else:
            expenses.order_by("date", "id")

        user_id = filter_data.get("user")
        user_id = int(user_id) if user_id not in (None, "") else None
    else:
        expenses = ExpenseEntry.objects.all().order_by("date", "id")
        user_id = None

    summary = calculate_summary_expenses(expenses)
    users = CustomUser.objects.filter(is_active=True)
    page = request.GET.get("page")
    pagination = Paginator(expenses, per_page=10).get_page(page)

    context = {
        "page": "activity",
        "subpage": "expenses",
        "edit": False,
        "objects": pagination.object_list,
        "pagination": pagination,
        "number_expenses": number_expenses,
        "summary": summary,
        "users": users,
        "user_id": user_id,
    }

    return render(request, "activity/list.html", context)


@login_required
def filter_expenses(request):
    def get_filter(request):
        filter_data = request.session.get("expense_filter", request.POST)

        return ExpenseFilter(filter_data, queryset=ExpenseEntry.objects.all())

    if request.method == "POST":
        request.session["expense_filter"] = request.POST

        return redirect("activity:list")
    else:
        filter = get_filter(request)

        return render(request, "activity/expenses-filter.html", {"filter": filter})


@login_required
def quick_filter_expenses(request, tab):
    if tab == "time":
        filter_data = request.session.get("time_filter", {})
    elif tab == "expenses":
        filter_data = request.session.get("expense_filter", {})

    new_values = {
        "firm": "Campbell & Brannon",
        "matter": None,
        "keyword": "",
        "comp": None,
        "order": "date, ascending",
    }

    for key, val in new_values.items():
        filter_data[key] = val

    filter_data["entered"] = 0
    filter_data["invoice"] = 0
    filter_data["date_min"] = ""
    filter_data["date_max"] = ""

    if tab == "time":
        request.session["time_filter"] = filter_data
    elif tab == "expenses":
        request.session["expense_filter"] = filter_data

    request.session.modified = True

    return redirect("activity:list")


@login_required
def quick_filter_user(request, tab):
    if tab == "time":
        filter_data = request.session.get("time_filter", {})
    elif tab == "expenses":
        filter_data = request.session.get("expense_filter", {})

    user = request.POST.get("user")
    filter_data["user"] = user

    if tab == "time":
        request.session["time_filter"] = filter_data
    elif tab == "expenses":
        request.session["expense_filter"] = filter_data

    return redirect("activity:list")


@login_required
def add_expense(request, id=None):
    # if applicable, process any post data submitted by user
    if request.method == "POST":
        form = ExpenseEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user_id = request.user.id
            codes = {
                "ff ": "Filing fee ",
                "fx ": "FedEx ",
                "ml ": "Mail ",
            }
            for key, val in codes.items():
                entry.description = entry.description.replace(key, val)
            entry.save()
            return redirect("/activity")

    # if no post data has been submitted, show the entry form
    else:
        today = date.today().strftime("%Y-%m-%d")
        if id:
            matter = get_object_or_404(Matter, pk=id)
            form = ExpenseEntryForm(
                initial={
                    "date": today,
                    "matter": matter,
                }
            )
        else:
            form = ExpenseEntryForm(initial={"date": today})

    # get list of matters for activity form
    matter_list = Matter.objects.filter(status="Open").order_by("name")

    # if a single matter is selected,  pull that matter as a quersyset
    if id:
        selected_matter = Matter.objects.filter(id=id)

        # if the matter is closed, add it to the matter list
        # if it is open, don't add it; avoid creating two instances of the same matter
        if selected_matter.first().status == "Closed":
            matter_list |= selected_matter

    # set the form fields
    form.fields["matter"].queryset = matter_list

    context = {
        "page": "activity",
        "edit": False,
        "add": True,
        "action": "/activity/add_expense",
        "form": form,
        "matter_list": matter_list,
    }

    return render(request, "activity/form_expense.html", context)


@login_required
def edit_expense(request, id):
    entry = get_object_or_404(ExpenseEntry, pk=id)

    if request.method == "POST":
        form = ExpenseEntryForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.save()
            return redirect("/activity")

    else:
        # get list of matters for activity form
        matter_list = Matter.objects.filter(status="Open").order_by("name")

        selected_matter = Matter.objects.filter(id=entry.matter.id)
        if selected_matter.first().status == "Closed":
            matter_list |= selected_matter

        # initialize form
        form = ExpenseEntryForm(instance=entry)

        # set the form fields
        form.fields["matter"].queryset = matter_list

    context = {
        "page": "activity",
        "edit": True,
        "add": False,
        "action": f"/activity/{id}/edit_expense",
        "entry": entry,
        "form": form,
        "matter_list": matter_list,
    }

    return render(request, "activity/form_expense.html", context)


@login_required
def delete_expense(request, id):
    entry = get_object_or_404(ExpenseEntry, pk=id)
    entry.delete()
    return redirect("/activity")


@login_required
def toggle_entered_expenses(request, id):
    entry = get_object_or_404(ExpenseEntry, pk=id)
    if entry.entered == 1:
        entry.entered = 0
    else:
        entry.entered = 1
    entry.save()
    return redirect("/activity")
