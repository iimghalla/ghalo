rom decimal import Decimal, InvalidOperation

import streamlit as st


CATALOG = {
    1: {"name": "Gummy Bears", "price": Decimal("35.00")},
    2: {"name": "Strawberry Gummies", "price": Decimal("25.00")},
    3: {"name": "Cola Bottles Gummies", "price": Decimal("30.00")},
    4: {"name": "Jelly Beans", "price": Decimal("20.00")},
}
DISCOUNT_THRESHOLD = Decimal("100.00")
DISCOUNT_RATE = Decimal("0.10")


def money(amount: Decimal) -> str:
    return f"SAR {amount:,.2f}"


def clear_receipt() -> None:
    st.session_state.receipt = None
    st.session_state.calculation_error = None


def add_order() -> None:
    name = st.session_state.get("customer_name", "").strip()
    item_number = st.session_state.get("item_number", "").strip()
    quantity_text = st.session_state.get("quantity_kg", "").strip()

    if not name:
        st.session_state.order_error = "Please enter your name"
        st.session_state.order_notice = None
        return

    try:
        item_id = int(item_number)
    except ValueError:
        st.session_state.order_error = (
            "Invalid item number. Please choose from 1 to 4"
        )
        st.session_state.order_notice = None
        return

    if item_id not in CATALOG:
        st.session_state.order_error = (
            "Invalid item number. Please choose from 1 to 4"
        )
        st.session_state.order_notice = None
        return

    try:
        quantity = Decimal(quantity_text)
    except InvalidOperation:
        quantity = Decimal("0")

    if not quantity.is_finite() or quantity <= 0:
        st.session_state.order_error = "Please enter a valid quantity"
        st.session_state.order_notice = None
        return

    order_id = st.session_state.next_order_id
    st.session_state.orders.append(
        {
            "id": order_id,
            "item_id": item_id,
            "name": CATALOG[item_id]["name"],
            "price": CATALOG[item_id]["price"],
            "quantity": quantity,
        }
    )
    st.session_state.next_order_id += 1
    st.session_state.item_number = ""
    st.session_state.quantity_kg = ""
    st.session_state.order_error = None
    st.session_state.order_notice = f"{CATALOG[item_id]['name']} added to your order."
    clear_receipt()


def remove_order(order_id: int) -> None:
    st.session_state.orders = [
        order for order in st.session_state.orders if order["id"] != order_id
    ]
    st.session_state.order_notice = None
    st.session_state.order_error = None
    clear_receipt()


def calculate_receipt() -> None:
    name = st.session_state.get("customer_name", "").strip()
    orders = st.session_state.orders

    if not name:
        st.session_state.calculation_error = "Please enter your name"
        st.session_state.receipt = None
        return

    if not orders:
        st.session_state.calculation_error = "Please add at least one order"
        st.session_state.receipt = None
        return

    subtotal = sum(
        (order["price"] * order["quantity"] for order in orders),
        start=Decimal("0.00"),
    )
    discount = subtotal * DISCOUNT_RATE if subtotal >= DISCOUNT_THRESHOLD else Decimal("0.00")
    st.session_state.receipt = {
        "customer_name": name,
        "orders": [order.copy() for order in orders],
        "subtotal": subtotal,
        "discount": discount,
        "total": subtotal - discount,
    }
    st.session_state.calculation_error = None


st.set_page_config(page_title="Sugar & Sprinkles Candy Shop", layout="centered")

for key, default in (
    ("orders", []),
    ("next_order_id", 1),
    ("receipt", None),
    ("order_error", None),
    ("order_notice", None),
    ("calculation_error", None),
):
    if key not in st.session_state:
        st.session_state[key] = default

st.title("Sugar & Sprinkles")
st.caption("Choose your favorites by the kilogram and get a clear receipt at checkout.")

st.text_input(
    "Customer name",
    key="customer_name",
    placeholder="Enter your name",
    on_change=clear_receipt,
)

menu_column, order_column = st.columns([1, 1], gap="large")

with menu_column:
    with st.container(border=True):
        st.subheader("Candy menu")
        st.caption("Prices are per kilogram")
        for item_id, item in CATALOG.items():
            st.write(f"**{item_id}. {item['name']}**")
            st.write(money(item["price"]))
            if item_id != len(CATALOG):
                st.divider()

    with st.container(border=True):
        st.subheader("Add to your order")
        with st.form("add_order_form"):
            st.text_input("Candy item number", key="item_number", placeholder="1–4")
            st.text_input("Quantity in kilograms", key="quantity_kg", placeholder="For example, 0.5")
            st.form_submit_button(
                "Add Order",
                type="primary",
                on_click=add_order,
                use_container_width=True,
            )

        if st.session_state.order_error:
            st.error(st.session_state.order_error)
        if st.session_state.order_notice:
            st.success(st.session_state.order_notice)

with order_column:
    with st.container(border=True):
        st.subheader("Your order")
        if not st.session_state.orders:
            st.caption("Your order list is empty.")
        else:
            for order in st.session_state.orders:
                item_total = order["price"] * order["quantity"]
                item_column, remove_column = st.columns([5, 1])
                with item_column:
                    st.write(f"**{order['name']}**")
                    st.caption(
                        f"{order['quantity']:,.3f} kg × {money(order['price'])}/kg"
                    )
                    st.write(money(item_total))
                with remove_column:
                    st.button(
                        "X",
                        key=f"remove_{order['id']}",
                        help=f"Remove {order['name']} from your order",
                        on_click=remove_order,
                        args=(order["id"],),
                    )

        st.button(
            "Calculate Final Total",
            type="primary",
            use_container_width=True,
            on_click=calculate_receipt,
        )
        if st.session_state.calculation_error:
            st.error(st.session_state.calculation_error)

if st.session_state.receipt:
    receipt = st.session_state.receipt
    st.divider()
    with st.container(border=True):
        st.subheader("Receipt")
        st.write(f"**Customer:** {receipt['customer_name']}")
        st.divider()

        for order in receipt["orders"]:
            line_total = order["price"] * order["quantity"]
            st.write(
                f"**{order['name']}** — {order['quantity']:,.3f} kg "
                f"× {money(order['price'])}/kg = {money(line_total)}"
            )

        st.divider()
        st.write(f"**Subtotal:** {money(receipt['subtotal'])}")
        st.write(f"**Discount:** −{money(receipt['discount'])}")
        st.markdown(f"### Final total: {money(receipt['total'])}")
        st.success("Thank you for your order.")
