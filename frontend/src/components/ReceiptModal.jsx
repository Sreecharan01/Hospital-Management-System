import React from 'react';
import { X, Printer, ShieldCheck, CheckCircle2, Building2, Calendar, Clock, User } from 'lucide-react';

export default function ReceiptModal({ receipt, onClose }) {
  if (!receipt) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-xl w-full shadow-2xl border border-gray-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Top Bar */}
        <div className="bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/10 rounded-xl backdrop-blur-md">
              <CheckCircle2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight">Consultation Fee Receipt</h2>
              <p className="text-xs text-emerald-100">Official Electronic Healthcare Tax Invoice</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Printable Receipt Body */}
        <div className="p-6 sm:p-8 space-y-6 printable-receipt">
          {/* Hospital Header */}
          <div className="flex justify-between items-start border-b border-gray-100 pb-5">
            <div>
              <div className="flex items-center space-x-2 text-primary-700 font-extrabold text-lg">
                <Building2 className="w-5 h-5 text-primary-600" />
                <span>{receipt.hospital?.name || 'CityCare Central Hospital'}</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">{receipt.hospital?.address || '742 Healthcare Ave, Medical District'}</p>
              <p className="text-xs text-gray-500">Contact: {receipt.hospital?.support_phone || '+1 (800) 555-CARE'}</p>
            </div>
            <div className="text-right">
              {receipt.status === 'REFUND_PENDING' ? (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300">
                  ⏳ 50% REFUND PENDING
                </span>
              ) : receipt.status === 'REFUNDED' ? (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-900 border border-purple-300">
                  ✓ 50% REFUNDED
                </span>
              ) : (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  ✓ {receipt.status || 'PAID'}
                </span>
              )}
              <p className="text-xs font-mono font-bold text-gray-700 mt-2">#{receipt.receipt_number}</p>
              <p className="text-[11px] text-gray-400 mt-0.5">{receipt.paid_at}</p>
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 gap-4 text-xs bg-gray-50 p-4 rounded-xl border border-gray-100">
            <div>
              <p className="text-gray-400 font-semibold uppercase tracking-wider text-[10px]">Patient Details</p>
              <p className="font-bold text-gray-800 text-sm mt-0.5">{receipt.patient?.name}</p>
              <p className="text-gray-600">{receipt.patient?.email}</p>
              <p className="text-gray-600">Phone: {receipt.patient?.phone}</p>
            </div>
            <div>
              <p className="text-gray-400 font-semibold uppercase tracking-wider text-[10px]">Consulting Doctor</p>
              <p className="font-bold text-gray-800 text-sm mt-0.5">{receipt.doctor?.name}</p>
              <p className="text-primary-600 font-medium">{receipt.doctor?.specialty}</p>
              <p className="text-gray-500">{receipt.doctor?.email}</p>
            </div>
          </div>

          {/* Consultation Item Table */}
          <div className="border border-gray-100 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 text-gray-500 font-semibold border-b border-gray-100">
                <tr>
                  <th className="py-2.5 px-4">Service Description</th>
                  <th className="py-2.5 px-4">Slot Time</th>
                  <th className="py-2.5 px-4 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                <tr>
                  <td className="py-3 px-4">
                    <p className="font-semibold text-gray-900">Doctor Medical Consultation</p>
                    <p className="text-[11px] text-gray-500">Date: {receipt.appointment?.date}</p>
                  </td>
                  <td className="py-3 px-4 text-gray-600 font-medium">
                    {receipt.appointment?.time || 'Scheduled slot'}
                  </td>
                  <td className="py-3 px-4 text-right font-bold text-gray-900">
                    ₹{parseFloat(receipt.amount || 0).toFixed(2)}
                  </td>
                </tr>
                <tr className="bg-gray-50/50">
                  <td className="py-2 px-4 text-gray-500 text-[11px]">Electronic Tele-Registration & Tax</td>
                  <td className="py-2 px-4 text-gray-400">Included</td>
                  <td className="py-2 px-4 text-right text-gray-500">₹0.00</td>
                </tr>
                {receipt.refund_amount > 0 && (
                  <>
                    <tr className="bg-amber-50/40 text-amber-900 font-medium">
                      <td className="py-2 px-4 text-[11px]">
                        Cancellation 50% Refund ({receipt.status === 'REFUNDED' ? 'Refunded' : 'Pending Admin Initiation'})
                      </td>
                      <td className="py-2 px-4 text-amber-700 text-[11px]">50% Policy</td>
                      <td className="py-2 px-4 text-right text-amber-800">
                        -₹{parseFloat(receipt.refund_amount || 0).toFixed(2)}
                      </td>
                    </tr>
                    <tr className="bg-gray-50/40 text-gray-500 text-[11px]">
                      <td className="py-1.5 px-4">Hospital Retained Fee (50%)</td>
                      <td className="py-1.5 px-4">Cancellation Fee</td>
                      <td className="py-1.5 px-4 text-right">
                        ₹{(parseFloat(receipt.amount || 0) - parseFloat(receipt.refund_amount || 0)).toFixed(2)}
                      </td>
                    </tr>
                  </>
                )}
              </tbody>
              <tfoot className="bg-emerald-50/60 border-t border-emerald-100 text-emerald-950 font-bold">
                <tr>
                  <td colSpan="2" className="py-3 px-4 text-sm">
                    {receipt.refund_amount > 0 ? 'Total Net Paid (After 50% Refund)' : 'Total Paid'}
                  </td>
                  <td className="py-3 px-4 text-right text-base text-emerald-700">
                    ₹{receipt.refund_amount > 0
                      ? (parseFloat(receipt.amount || 0) - parseFloat(receipt.refund_amount || 0)).toFixed(2)
                      : parseFloat(receipt.amount || 0).toFixed(2)}{' '}
                    {receipt.currency || 'INR'}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Payment Method & Transaction Info */}
          <div className="bg-blue-50/60 p-3.5 rounded-xl border border-blue-100/80 flex items-center justify-between text-xs text-blue-900">
            <div>
              <p className="font-semibold">Payment Method: {receipt.payment_method}</p>
              {receipt.card_last4 && (
                <p className="text-[11px] text-blue-700">Card ending in •••• {receipt.card_last4} ({receipt.card_brand})</p>
              )}
              {receipt.upi_id && (
                <p className="text-[11px] text-blue-700">UPI ID: {receipt.upi_id}</p>
              )}
              {receipt.refund_transaction_id && (
                <p className="text-[11px] text-purple-700 font-semibold mt-0.5">
                  50% Refund Ref: {receipt.refund_transaction_id}
                </p>
              )}
            </div>
            <div className="text-right">
              <span className="text-[10px] text-blue-600 uppercase tracking-wider block">Transaction Ref</span>
              <span className="font-mono font-bold text-blue-800 text-[11px]">{receipt.transaction_id}</span>
            </div>
          </div>

          {/* Footer Notice */}
          <div className="text-center text-[11px] text-gray-400 pt-1">
            <p className="flex items-center justify-center space-x-1">
              <ShieldCheck className="w-4 h-4 text-emerald-500 inline" />
              <span>Verified Secure Transaction • Tax ID: {receipt.hospital?.tax_id || 'MED-TAX-2026-9812'}</span>
            </p>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-100 flex items-center justify-between">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-semibold text-gray-600 hover:text-gray-900 transition"
          >
            Close
          </button>
          <button
            type="button"
            onClick={handlePrint}
            className="btn-primary inline-flex items-center space-x-2 px-5 py-2 text-sm shadow-md"
          >
            <Printer className="w-4 h-4" />
            <span>Print Receipt</span>
          </button>
        </div>

      </div>
    </div>
  );
}

