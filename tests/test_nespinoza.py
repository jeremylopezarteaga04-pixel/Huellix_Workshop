"""Prueba 4: integración top-down, CLI + OrderService con pago aprobado (IVA).

- Clasificación: integración top-down.
- Capa de inicio: CLI (app.cli.main).
- Componentes reales: app.cli (main/run_order) y OrderService.
- Dobles: FakeDb (base de datos en memoria), Mock(spec=PaymentGateway)
  para la pasarela, y parches de build_service y builtins.input.
"""

from app import cli
from app.order_service import OrderService
from app.payment_gateway import PaymentGateway
from tests.support.fake_db import FakeDb


def test_cli_servicio_pago_aprobado_calcula_iva(mocker, capsys):
    db = FakeDb(stock={"LAPIZ": 10}, prices={"LAPIZ": 1.25})
    pasarela = mocker.Mock(spec=PaymentGateway)
    pasarela.charge.return_value = {"approved": True, "transaction_id": "tx_999"}

    # CLI y OrderService reales; solo se inyectan los dobles de BD y pasarela.
    mocker.patch("app.cli.build_service", return_value=OrderService(db, pasarela))
    mocker.patch("builtins.input", side_effect=["LAPIZ", "4", "tok_ok"])

    codigo = cli.main()

    assert codigo == 0
    assert capsys.readouterr().out == "OK: pedido ORD-1 confirmado, total=5.8\n"
    pasarela.charge.assert_called_once_with("tok_ok", 5.8)
    pedido = db.orders["ORD-1"]
    assert pedido["product_id"] == "LAPIZ"
    assert pedido["quantity"] == 4
    assert pedido["total"] == 5.8
    assert pedido["transaction_id"] == "tx_999"
