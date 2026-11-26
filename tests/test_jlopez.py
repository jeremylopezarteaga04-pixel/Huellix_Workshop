import pytest

from app.order_service import OrderService, PaymentRejectedError
from app.payment_gateway import PaymentGateway
from tests.support.fake_db import FakeDb

CHARGES_URL = "https://payments.example.com/api/v1/charges"


def test_pago_rechazado_no_registra_pedido_ni_toca_inventario(requests_mock):
    """Prueba de integración BOTTOM-UP.

    - Clasificación: bottom-up. Se parte de la capa más baja (PaymentGateway,
      cliente HTTP real) y se integra hacia arriba con OrderService real.
    - Componentes reales: PaymentGateway y OrderService.
    - Dobles usados: FakeDb (sustituye la base de datos) y requests_mock
      (simula la respuesta HTTP 402 del proveedor de pagos).
    - Regla comprobada: si la pasarela rechaza el pago, el servicio lanza
      PaymentRejectedError, NO guarda el pedido y NO modifica el inventario.
    """
    db = FakeDb(stock={"CUADERNO": 5}, prices={"CUADERNO": 3.0})
    servicio = OrderService(db, PaymentGateway())

    requests_mock.post(
        CHARGES_URL,
        status_code=402,
        json={"reason": "insufficient_funds"},
    )

    with pytest.raises(PaymentRejectedError):
        servicio.place_order("CUADERNO", 2, "tok_sin_fondos")

    assert db.orders == {}
    assert db.get_stock("CUADERNO") == 5
