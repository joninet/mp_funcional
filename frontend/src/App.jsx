import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [amount, setAmount] = useState('')
  const [qrInfo, setQrInfo] = useState(null)
  const [currentOrderId, setCurrentOrderId] = useState(null)
  const [paymentStatus, setPaymentStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  
  const paymentCheckInterval = useRef(null)

  // Función para verificar el estado del pago
  const checkPaymentStatus = async (orderId) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/payments/check-order/${orderId}/`)
      const data = await response.json()
      
      if (response.ok) {
        const status = data.status
        setPaymentStatus(status)
        
        if (status === 'approved') {
          setMessage(`¡Pago confirmado! Monto de $${amount} recibido.`)
          clearInterval(paymentCheckInterval.current)
          paymentCheckInterval.current = null
        } else if (status === 'rejected' || status === 'cancelled') {
          setMessage('El pago fue rechazado o cancelado.')
          clearInterval(paymentCheckInterval.current)
          paymentCheckInterval.current = null
        } else if (status === 'pending' || status === 'in_process') {
          // Continuar verificando
          setMessage(`Monto de $${amount} cargado. Esperando confirmación del pago...`)
        }
      }
    } catch (error) {
      console.error('Error verificando pago:', error)
    }
  }

  // Función para iniciar la verificación de pago
  const startPaymentCheck = (orderId) => {
    // Verificar inmediatamente
    checkPaymentStatus(orderId)
    
    // Luego verificar cada 3 segundos
    paymentCheckInterval.current = setInterval(() => {
      checkPaymentStatus(orderId)
    }, 3000)
  }

  // Limpiar intervalo cuando el componente se desmonte
  useEffect(() => {
    return () => {
      if (paymentCheckInterval.current) {
        clearInterval(paymentCheckInterval.current)
      }
    }
  }, [])

  useEffect(() => {
    // Obtener información del QR al cargar
    fetch('http://127.0.0.1:8000/api/payments/qr-info/')
      .then(res => res.json())
      .then(data => setQrInfo(data))
      .catch(err => console.error("Error cargando QR:", err))
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!amount || isNaN(amount)) return
    
    // Limpiar estado anterior
    if (paymentCheckInterval.current) {
      clearInterval(paymentCheckInterval.current)
    }
    setAmount('')
    setCurrentOrderId(null)
    setPaymentStatus(null)
    
    setLoading(true)
    setMessage('Cargando monto al QR...')
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/payments/create-order/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ amount }),
      })
      
      const data = await response.json()
      
      if (response.ok) {
        // Almacenar el ID de la orden para verificar estado
        if (data.external_reference) {
          setCurrentOrderId(data.external_reference)  // Usar external_reference para verificar pagos
          setPaymentStatus('pending')
          // Iniciar verificación de pago
          startPaymentCheck(data.external_reference)
        }
        setMessage(`Monto de $${amount} cargado. ¡Escanea el QR fijo para pagar!`)
      } else {
        setMessage(`Error: ${data.error || 'No se pudo crear la orden'}`)
      }
    } catch (error) {
      setMessage('Error de conexión con el servidor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Punto de Venta - Verdulería</h1>
      
      <div className="pos-card">
        {qrInfo ? (
          <div className="qr-section">
            <h3>Escanea aquí para pagar</h3>
            <img src={qrInfo.qr_image} alt="QR Mercado Pago" className="qr-image" />
            <p><small>ID Caja: {qrInfo.external_pos_id}</small></p>
            <p><strong>QR Fijo (Impreso)</strong></p>
          </div>
        ) : (
          <p>Cargando información del QR...</p>
        )}

        <form onSubmit={handleSubmit} className="payment-form">
          <div className="input-group">
            <label htmlFor="amount">Total a Cobrar:</label>
            <input
              type="number"
              id="amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              step="0.01"
              required
            />
          </div>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Procesando...' : 'Cargar Monto'}
          </button>
        </form>

        {message && <div className="status-message">{message}</div>}
        
        {paymentStatus && (
          <div className={`payment-status ${paymentStatus}`}>
            <h4>Estado del Pago: 
              <span className={`status-${paymentStatus}`}>
                {paymentStatus === 'pending' && '⏳ Pendiente'}
                {paymentStatus === 'approved' && '✅ Aprobado'}
                {paymentStatus === 'in_process' && '🔄 Procesando'}
                {paymentStatus === 'rejected' && '❌ Rechazado'}
                {paymentStatus === 'cancelled' && '❌ Cancelado'}
                {paymentStatus === 'authorized' && '✅ Autorizado'}
                {!['pending', 'approved', 'in_process', 'rejected', 'cancelled', 'authorized'].includes(paymentStatus) && paymentStatus}
              </span>
            </h4>
          </div>
        )}
      </div>
      
      <div className="test-accounts">
        <h4>Cuentas de Prueba:</h4>
        <p><strong>Vendedor:</strong> TESTUSER2040611109</p>
        <p><strong>Comprador:</strong> TESTUSER1350721340</p>
      </div>
    </div>
  )
}

export default App
