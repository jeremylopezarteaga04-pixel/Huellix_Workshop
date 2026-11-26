# Prueba de integración bottom-up — J. Salaza
from app.order_service import OrderService
from app.payment_gateway import PaymentGateway
from tests.support.fake_db import FakeDb


def test_pago_aprobado_bottom_up(requests_mock):
    """Prueba de integración bottom-up: PaymentGateway + OrderService con pago aprobado.

    - Estrategia: bottom-up (se integra la capa 3 real PaymentGateway con la capa 2
      real OrderService, sin llegar a la CLI).
    - Componentes reales: PaymentGateway y OrderService.
    - Dobles usados: FakeDb en memoria (sustituye a DbConnector) y requests_mock
      (intercepta la petición HTTP al proveedor externo de pagos).
    - Comportamiento comprobado: al aprobarse el pago con HTTP 200, el servicio
      calcula el total con IVA (17.4), envía el payload correcto a la pasarela,
      confirma el pedido, registra la orden con su transaction_id en FakeDb y
      descuenta el stock a 7 unidades.
    """
    db = FakeDb(stock={"TAZA": 9}, prices={"TAZA": 7.5})
    requests_mock.post(
        "https://payments.example.com/api/v1/charges",
        status_code=200,
        json={"transaction_id": "tx_123"},
    )

    gateway = PaymentGateway()
    service = OrderService(db, gateway)

    result = service.place_order("TAZA", 2, "tok_ok")

    assert result["status"] == "CONFIRMED"
    assert result["total"] == 17.4
    assert len(db.orders) == 1
    saved_order = next(iter(db.orders.values()))
    assert saved_order["transaction_id"] == "tx_123"
    assert requests_mock.last_request.json() == {
        "card_token": "tok_ok",
        "amount": 17.4,
    }
    assert db.get_stock("TAZA") == 7
