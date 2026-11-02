import React, { useState } from 'react';
import {
  CreditCard,
  QrCode,
  Building2,
  Lock,
  ShieldCheck,
  CheckCircle2,
  X,
  Sparkles,
  ArrowRight,
  Clock,
  Calendar,
  AlertCircle
} from 'lucide-react';

export default function PaymentModal({
  isOpen,
  onClose,
  amount,
  doctorName,
  specialty,
  appointmentDate,
  appointmentTime,
  onConfirmPayment,
  loading = false
}) {
  const [method, setMethod] = useState('CARD'); // 'CARD' | 'UPI' | 'NETBANKING'
  
  // Card form state
  const [cardNumber, setCardNumber] = useState('');
  const [cardName, setCardName] = useState('');
  const [cardExpiry, setCardExpiry] = useState('');
  const [cardCvv, setCardCvv] = useState('');

  // UPI form state
  const [upiId, setUpiId] = useState('');

  // Net banking state
  const [selectedBank, setSelectedBank] = useState('HDFC');

  // Processing animation state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState('');

  if (!isOpen) return null;

  const feeAmount = parseFloat(amount || 0).toFixed(2);

  // Auto-format card number with spaces every 4 digits
  const handleCardNumberChange = (e) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 16);
    const formatted = raw.replace(/(\d{4})/g, '$1 ').trim();
    setCardNumber(formatted);
  };

  // Auto-format expiry MM/YY
  const handleExpiryChange = (e) => {
    let raw = e.target.value.replace(/\D/g, '').slice(0, 4);
    if (raw.length >= 3) {
      raw = raw.slice(0, 2) + '/' + raw.slice(2, 4);
    }
    setCardExpiry(raw);
  };

  // Demo auto-fill helpers
  const handleFillDemoCard = () => {
    setCardNumber('4242 4242 4242 4242');
    setCardName('Jane Doe');
    setCardExpiry('12/28');
    setCardCvv('123');
  };

  const handleFillDemoUPI = () => {
    setUpiId('patient.health@okhdfcbank');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (method === 'CARD') {
      const cleanNum = cardNumber.replace(/\s/g, '');
      if (cleanNum.length < 15) {
        alert('Please enter a valid 16-digit card number.');
        return;
      }
      if (!cardName.trim()) {
        alert('Please enter cardholder name.');
        return;
      }
      if (cardExpiry.length < 5) {
        alert('Please enter expiry in MM/YY format.');
        return;
      }
      if (cardCvv.length < 3) {
        alert('Please enter CVV.');
        return;
      }
    } else if (method === 'UPI') {
      if (!upiId.includes('@')) {
        alert('Please enter a valid UPI ID (e.g. name@bank).');
        return;
      }
    }

    setIsProcessing(true);
    setProcessingStage('Connecting to secure payment gateway...');

    setTimeout(() => {
      setProcessingStage('Authenticating with payment network...');
    }, 800);

    setTimeout(() => {
      setProcessingStage('Authorizing payment approval...');
    }, 1600);

    setTimeout(async () => {
      setIsProcessing(false);
      const cleanCard = cardNumber.replace(/\s/g, '');
      const payload = {
        payment_method: method,
        card_last4: method === 'CARD' ? cleanCard.slice(-4) : undefined,
        card_brand: method === 'CARD' ? (cleanCard.startsWith('4') ? 'Visa' : 'Mastercard') : undefined,
        upi_id: method === 'UPI' ? upiId : undefined,
        bank: method === 'NETBANKING' ? selectedBank : undefined,
        amount: feeAmount,
      };
      await onConfirmPayment(payload);
    }, 2400);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl border border-gray-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Top Header */}
        <div className="bg-gradient-to-r from-primary-600 via-primary-700 to-indigo-800 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-white/10 rounded-2xl backdrop-blur-md">
              <Lock className="w-5 h-5 text-emerald-300" />
            </div>
            <div>
              <h2 className="text-lg font-bold">Consultation Fee Checkout</h2>
              <p className="text-xs text-primary-200 flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-300 inline" />
                <span>256-Bit SSL Encrypted Healthcare Payment</span>
              </p>
            </div>
          </div>
          {!isProcessing && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Consultation Summary Banner */}
        <div className="bg-gray-50 border-b border-gray-100 px-6 py-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Booking with</p>
            <p className="font-bold text-gray-900 text-sm">{doctorName || 'Doctor'}</p>
            <p className="text-xs text-primary-600 font-medium">{specialty || 'General'}</p>
          </div>
          <div className="text-right">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Consultation Fee</p>
            <p className="text-2xl font-black text-emerald-600">₹{feeAmount}</p>
          </div>
        </div>

        {isProcessing ? (
          /* Processing State Animation */
          <div className="p-12 text-center space-y-6">
            <div className="relative w-20 h-20 mx-auto">
              <div className="w-20 h-20 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
              <Lock className="w-8 h-8 text-primary-600 absolute inset-0 m-auto" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Processing Payment</h3>
              <p className="text-sm text-primary-600 font-medium mt-1 animate-pulse">
                {processingStage}
              </p>
              <p className="text-xs text-gray-400 mt-3">Please do not refresh or close this window.</p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {/* Payment Method Selector Tabs */}
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                Choose Payment Method
              </label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setMethod('CARD')}
                  className={`flex flex-col items-center justify-center py-3 px-2 rounded-xl border text-xs font-bold transition ${
                    method === 'CARD'
                      ? 'border-primary-600 bg-primary-50/70 text-primary-700 shadow-sm'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600 bg-white'
                  }`}
                >
                  <CreditCard className="w-5 h-5 mb-1 text-primary-600" />
                  <span>Card</span>
                </button>

                <button
                  type="button"
                  onClick={() => setMethod('UPI')}
                  className={`flex flex-col items-center justify-center py-3 px-2 rounded-xl border text-xs font-bold transition ${
                    method === 'UPI'
                      ? 'border-primary-600 bg-primary-50/70 text-primary-700 shadow-sm'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600 bg-white'
                  }`}
                >
                  <QrCode className="w-5 h-5 mb-1 text-indigo-600" />
                  <span>UPI / QR</span>
                </button>

                <button
                  type="button"
                  onClick={() => setMethod('NETBANKING')}
                  className={`flex flex-col items-center justify-center py-3 px-2 rounded-xl border text-xs font-bold transition ${
                    method === 'NETBANKING'
                      ? 'border-primary-600 bg-primary-50/70 text-primary-700 shadow-sm'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600 bg-white'
                  }`}
                >
                  <Building2 className="w-5 h-5 mb-1 text-teal-600" />
                  <span>Net Banking</span>
                </button>
              </div>
            </div>

            {/* TAB 1: CARD PAYMENT */}
            {method === 'CARD' && (
              <div className="space-y-3.5 bg-gray-50/70 p-4 rounded-2xl border border-gray-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-600">Card Information</span>
                  <button
                    type="button"
                    onClick={handleFillDemoCard}
                    className="text-[11px] font-bold text-primary-600 hover:text-primary-700 underline"
                  >
                    ⚡ Fill Demo Test Card
                  </button>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-gray-500 mb-1">Card Number</label>
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="4242 4242 4242 4242"
                      value={cardNumber}
                      onChange={handleCardNumberChange}
                      className="input pl-10 font-mono text-sm tracking-wider"
                      required
                    />
                    <CreditCard className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" />
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-gray-500 mb-1">Cardholder Name</label>
                  <input
                    type="text"
                    placeholder="Full Name as on card"
                    value={cardName}
                    onChange={(e) => setCardName(e.target.value)}
                    className="input text-sm"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-gray-500 mb-1">Expiry Date</label>
                    <input
                      type="text"
                      placeholder="MM/YY"
                      value={cardExpiry}
                      onChange={handleExpiryChange}
                      className="input font-mono text-sm"
                      maxLength={5}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-gray-500 mb-1">CVV / CVC</label>
                    <input
                      type="password"
                      placeholder="•••"
                      value={cardCvv}
                      onChange={(e) => setCardCvv(e.target.value.replace(/\D/g, '').slice(0, 4))}
                      className="input font-mono text-sm"
                      maxLength={4}
                      required
                    />
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: UPI / QR PAYMENT */}
            {method === 'UPI' && (
              <div className="space-y-4 bg-gray-50/70 p-4 rounded-2xl border border-gray-100 text-center">
                <div className="flex justify-between items-center text-left">
                  <span className="text-xs font-semibold text-gray-600">Scan QR or enter UPI ID</span>
                  <button
                    type="button"
                    onClick={handleFillDemoUPI}
                    className="text-[11px] font-bold text-primary-600 hover:text-primary-700 underline"
                  >
                    ⚡ Fill Demo UPI ID
                  </button>
                </div>

                {/* Simulated QR Code */}
                <div className="bg-white p-4 rounded-2xl border border-gray-200 inline-block shadow-sm">
                  <div className="w-36 h-36 bg-gradient-to-br from-indigo-50 to-blue-50 border-2 border-dashed border-indigo-200 rounded-xl flex flex-col items-center justify-center p-2 text-indigo-700">
                    <QrCode className="w-16 h-16 opacity-80" />
                    <span className="text-[10px] font-bold mt-1">UPI Instant Scan</span>
                    <span className="text-[9px] text-gray-400">Accepts GPay, PhonePe, Paytm</span>
                  </div>
                </div>

                <div className="text-left">
                  <label className="block text-[11px] font-medium text-gray-500 mb-1">Virtual Payment Address (UPI ID)</label>
                  <input
                    type="text"
                    placeholder="username@okhdfcbank"
                    value={upiId}
                    onChange={(e) => setUpiId(e.target.value)}
                    className="input text-sm font-mono"
                    required
                  />
                  <div className="flex items-center space-x-2 mt-2">
                    {['@okhdfcbank', '@okaxis', '@paytm', '@ybl'].map((suffix) => (
                      <button
                        key={suffix}
                        type="button"
                        onClick={() => setUpiId((prev) => (prev ? prev.split('@')[0] + suffix : 'user' + suffix))}
                        className="text-[10px] font-medium bg-white border border-gray-200 px-2 py-0.5 rounded-md hover:bg-gray-100 text-gray-600"
                      >
                        {suffix}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: NET BANKING */}
            {method === 'NETBANKING' && (
              <div className="space-y-3 bg-gray-50/70 p-4 rounded-2xl border border-gray-100">
                <span className="text-xs font-semibold text-gray-600 block mb-2">Select Your Bank</span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { id: 'HDFC', name: 'HDFC Bank' },
                    { id: 'SBI', name: 'State Bank of India' },
                    { id: 'ICICI', name: 'ICICI Bank' },
                    { id: 'AXIS', name: 'Axis Bank' },
                    { id: 'CHASE', name: 'Chase Bank' },
                    { id: 'BOA', name: 'Bank of America' },
                  ].map((b) => (
                    <label
                      key={b.id}
                      className={`flex items-center space-x-2 p-2.5 rounded-xl border cursor-pointer transition ${
                        selectedBank === b.id
                          ? 'border-teal-600 bg-teal-50/70 font-bold text-teal-900'
                          : 'border-gray-200 bg-white hover:border-gray-300 text-gray-700'
                      }`}
                    >
                      <input
                        type="radio"
                        name="bank"
                        checked={selectedBank === b.id}
                        onChange={() => setSelectedBank(b.id)}
                        className="text-teal-600"
                      />
                      <span>{b.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Price breakdown */}
            <div className="space-y-1.5 text-xs text-gray-500 pt-1">
              <div className="flex justify-between">
                <span>Doctor Consultation Fee</span>
                <span>₹{feeAmount}</span>
              </div>
              <div className="flex justify-between">
                <span>Hospital Tele-Registration Fee</span>
                <span className="text-emerald-600 font-medium">Free (₹0.00)</span>
              </div>
              <div className="flex justify-between font-bold text-gray-900 text-sm border-t border-gray-100 pt-1.5">
                <span>Total Amount to Pay</span>
                <span className="text-emerald-600">₹{feeAmount} INR</span>
              </div>
            </div>

            {/* Cancellation Policy Notice */}
            <div className="bg-amber-50/80 border border-amber-200/80 rounded-xl p-2.5 flex items-start space-x-2 text-[11px] text-amber-800">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span>
                <strong>Cancellation & Refund Policy:</strong> If you cancel this appointment, a 50% refund (₹{(parseFloat(feeAmount) * 0.5).toFixed(2)}) will be initiated by the hospital administration.
              </span>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3.5 text-base font-bold shadow-lg shadow-primary-600/30 flex items-center justify-center space-x-2 rounded-2xl"
            >
              <ShieldCheck className="w-5 h-5" />
              <span>Pay ₹{feeAmount} & Confirm Booking</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>
          </form>
        )}

      </div>
    </div>
  );
}

