from app import cli
from app.order_service import OrderService
from app.payment_gateway import PaymentGateway
from tests.support.fake_db import FakeDb


def test_cli_rechaza_pedido_sin_stock(mocker, capsys):
    """Integración top-down.

    Capa de inicio: CLI (cli.main).
    Componente real incorporado: OrderService.
    Dobles usados: FakeDb (persistencia) y mocker.Mock(spec=PaymentGateway) (pasarela).
    """
    # Preparación
    db = FakeDb(stock={"CUADERNO": 1}, prices={"CUADERNO": 3.0})
    pasarela = mocker.Mock(spec=PaymentGateway)
    servicio = OrderService(db, pasarela)
    mocker.patch("app.cli.build_service", return_value=servicio)
    mocker.patch("builtins.input", side_effect=["cuaderno", "3", "tok_x"])

    # Ejecución
    codigo = cli.main()

    # Comprobaciones
    salida = capsys.readouterr().out
    assert codigo == 1
    assert salida.startswith("ERROR: sin stock")
    pasarela.charge.assert_not_called()
    assert db.orders == {}
    assert db.get_stock("CUADERNO") == 1
