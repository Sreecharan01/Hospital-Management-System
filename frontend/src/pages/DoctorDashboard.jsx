import { useState, useEffect } from 'react';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';
import StatusBadge from '../components/StatusBadge';
import toast from 'react-hot-toast';
import {
  Clock,
  Plus,
  Trash2,
  Calendar,
  CheckCircle,
  XCircle,
  UserX,
  FileText,
  X,
  Stethoscope,
  ClipboardList,
  ThumbsUp,
  TimerOff,
} from 'lucide-react';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function DoctorDashboard() {
  const { user } = useAuth();
  const [slots, setSlots] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [slotForm, setSlotForm] = useState({ day_of_week: '0', start_time: '09:00', end_time: '10:00' });
  const [addingSlot, setAddingSlot] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [recordModal, setRecordModal] = useState(null);
  const [recordForm, setRecordForm] = useState({ diagnosis: '', prescription: '', notes: '' });
  const [statusFilter, setStatusFilter] = useState('');

  const doctorId = user?.doctor_profile?.id;

  const fetchData = async () => {
    try {
      const [slotsRes, apptsRes] = await Promise.all([
        api.get('/slots/'),
        api.get('/appointments/'),
      ]);
      setSlots(slotsRes.data.results || slotsRes.data);
      setAppointments(apptsRes.data.results || apptsRes.data);
    } catch {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const activeSlots = slots.filter((s) => s.is_active);

  const filteredAppointments = statusFilter
    ? appointments.filter((a) => a.status === statusFilter)
    : appointments;

  // Slot management
  const handleAddSlot = async (e) => {
    e.preventDefault();
    setAddingSlot(true);
    try {
      await api.post('/slots/', slotForm);
      toast.success('Slot added');
      fetchData();
      setSlotForm({ day_of_week: '0', start_time: '09:00', end_time: '10:00' });
    } catch (err) {
      toast.error(err.response?.data?.detail || Object.values(err.response?.data || {}).flat().join(' ') || 'Failed to add slot');
    } finally {
      setAddingSlot(false);
    }
  };

  const handleDeleteSlot = async (slotId) => {
    if (!confirm('Deactivate this slot?')) return;
    try {
      await api.delete(`/slots/${slotId}/`);
      toast.success('Slot removed');
      fetchData();
    } catch {
      toast.error('Failed to delete slot');
    }
  };

  // Appointment actions
  const appointmentAction = async (id, action, label) => {
    setActionLoading(`${id}-${action}`);
    try {
      await api.post(`/appointments/${id}/${action}/`);
      toast.success(`Appointment ${label}`);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || `Failed to ${label}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Medical record
  const handleCreateRecord = async () => {
    if (!recordForm.diagnosis.trim()) {
      toast.error('Diagnosis is required');
      return;
    }
    setActionLoading('record');
    try {
      await api.post('/records/', {
        appointment_id: recordModal.id,
        ...recordForm,
      });
      toast.success('Medical record created');
      setRecordModal(null);
      setRecordForm({ diagnosis: '', prescription: '', notes: '' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create record');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return <LoadingSpinner size="lg" className="py-32" />;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Doctor Dashboard</h1>
        <p className="text-gray-500 mt-1">Manage your schedule and appointments</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* LEFT: Slot Manager */}
        <div className="space-y-6">
          {/* Add Slot */}
          <div className="card p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary-600" />
              Availability Slots
            </h2>

            <form onSubmit={handleAddSlot} className="space-y-3">
              <div>
                <label className="label">Day</label>
                <select
                  value={slotForm.day_of_week}
                  onChange={(e) => setSlotForm({ ...slotForm, day_of_week: e.target.value })}
                  className="input"
                >
                  {DAYS.map((d, i) => (
                    <option key={i} value={i}>{d}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Start</label>
                  <input
                    type="time"
                    value={slotForm.start_time}
                    onChange={(e) => setSlotForm({ ...slotForm, start_time: e.target.value })}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">End</label>
                  <input
                    type="time"
                    value={slotForm.end_time}
                    onChange={(e) => setSlotForm({ ...slotForm, end_time: e.target.value })}
                    className="input"
                  />
                </div>
              </div>
              <button type="submit" disabled={addingSlot} className="btn-primary w-full btn-sm">
                {addingSlot ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Add Slot
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Current Slots */}
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Active Slots ({activeSlots.length})</h3>
            {activeSlots.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">No slots added yet</p>
            ) : (
              <div className="space-y-2">
                {activeSlots.map((slot) => (
                  <div
                    key={slot.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-xl"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {DAYS[slot.day_of_week]}
                      </p>
                      <p className="text-xs text-gray-500">
                        {slot.start_time?.slice(0, 5)} – {slot.end_time?.slice(0, 5)}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDeleteSlot(slot.id)}
                      className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Appointments */}
        <div className="lg:col-span-2">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-primary-600" />
                Appointments ({filteredAppointments.length})
              </h2>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="input w-auto py-1.5 text-sm"
              >
                <option value="">All Statuses</option>
                <option value="PENDING">Pending</option>
                <option value="CONFIRMED">Confirmed</option>
                <option value="COMPLETED">Attended</option>
                <option value="CANCELLED">Cancelled</option>
                <option value="EXPIRED">Expired</option>
              </select>
            </div>

            {filteredAppointments.length === 0 ? (
              <div className="text-center py-12">
                <ClipboardList className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No appointments found</p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredAppointments.map((appt) => {
                  const isPending = appt.status === 'PENDING';
                  const isConfirmed = appt.status === 'CONFIRMED';
                  const isCompleted = appt.status === 'COMPLETED';
                  return (
                    <div key={appt.id} className="border border-gray-100 rounded-xl p-4 hover:bg-gray-50/50 transition-colors">
                      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className="font-medium text-gray-900">
                              {appt.patient_name || appt.patient_email || 'Patient'}
                            </p>
                            <StatusBadge status={appt.status} />
                            {appt.payment_status === 'PAID' ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                ✓ Fee Paid (${parseFloat(appt.doctor_fee || 0).toFixed(0)})
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                                Fee Unpaid
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3.5 h-3.5" />
                              {appt.date}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3.5 h-3.5" />
                              {appt.appointment_time?.slice(0, 5) || appt.slot?.start_time?.slice(0, 5)}
                            </span>
                          </div>
                          {appt.reason && (
                            <p className="text-xs text-gray-400 mt-1 truncate">Reason: {appt.reason}</p>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 shrink-0 flex-wrap">
                          {/* PENDING: Doctor can Accept or Decline */}
                          {isPending && (
                            <>
                              <button
                                onClick={() => appointmentAction(appt.id, 'confirm', 'confirmed')}
                                disabled={actionLoading === `${appt.id}-confirm`}
                                className="btn-sm bg-blue-50 text-blue-700 border border-blue-200 rounded-lg hover:bg-blue-100 inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 transition-colors"
                              >
                                <ThumbsUp className="w-3.5 h-3.5" />
                                Accept
                              </button>
                              <button
                                onClick={() => appointmentAction(appt.id, 'cancel', 'declined')}
                                disabled={actionLoading === `${appt.id}-cancel`}
                                className="btn-sm bg-red-50 text-red-700 border border-red-200 rounded-lg hover:bg-red-100 inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 transition-colors"
                              >
                                <XCircle className="w-3.5 h-3.5" />
                                Decline
                              </button>
                            </>
                          )}

                          {/* CONFIRMED: Doctor can mark Attended, Expired, or Cancel */}
                          {isConfirmed && (
                            <>
                              <button
                                onClick={() => appointmentAction(appt.id, 'complete', 'marked as attended')}
                                disabled={actionLoading === `${appt.id}-complete`}
                                className="btn-sm bg-green-50 text-green-700 border border-green-200 rounded-lg hover:bg-green-100 inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 transition-colors"
                              >
                                <CheckCircle className="w-3.5 h-3.5" />
                                Attended
                              </button>
                              <button
                                onClick={() => appointmentAction(appt.id, 'expire', 'marked as expired')}
                                disabled={actionLoading === `${appt.id}-expire`}
                                className="btn-sm bg-gray-50 text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-100 inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 transition-colors"
                              >
                                <TimerOff className="w-3.5 h-3.5" />
                                Expired
                              </button>
                              <button
                                onClick={() => appointmentAction(appt.id, 'cancel', 'cancelled')}
                                disabled={actionLoading === `${appt.id}-cancel`}
                                className="btn-sm bg-red-50 text-red-700 border border-red-200 rounded-lg hover:bg-red-100 inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 transition-colors"
                              >
                                <XCircle className="w-3.5 h-3.5" />
                                Cancel
                              </button>
                            </>
                          )}

                          {/* COMPLETED: Add medical record */}
                          {isCompleted && !appt.has_medical_record && (
                            <button
                              onClick={() => {
                                setRecordModal(appt);
                                setRecordForm({ diagnosis: '', prescription: '', notes: '' });
                              }}
                              className="btn-sm bg-accent-50 text-accent-700 border border-accent-200 rounded-lg hover:bg-accent-100 inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 transition-colors"
                            >
                              <FileText className="w-3.5 h-3.5" />
                              Add Record
                            </button>
                          )}
                          {isCompleted && appt.has_medical_record && (
                            <span className="text-xs text-green-600 flex items-center gap-1">
                              <CheckCircle className="w-3.5 h-3.5" /> Record exists
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Medical Record Modal */}
      {recordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 animate-scale-in">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-accent-600" />
                Add Medical Record
              </h3>
              <button onClick={() => setRecordModal(null)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="text-sm text-gray-500 mb-4 p-3 bg-gray-50 rounded-xl">
              Appointment on <strong>{recordModal.date}</strong> at{' '}
              <strong>{recordModal.appointment_time?.slice(0, 5) || recordModal.slot?.start_time?.slice(0, 5)}</strong>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Diagnosis *</label>
                <textarea
                  rows={3}
                  placeholder="Enter diagnosis..."
                  value={recordForm.diagnosis}
                  onChange={(e) => setRecordForm({ ...recordForm, diagnosis: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Prescription</label>
                <textarea
                  rows={3}
                  placeholder="Enter prescription..."
                  value={recordForm.prescription}
                  onChange={(e) => setRecordForm({ ...recordForm, prescription: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Notes</label>
                <textarea
                  rows={2}
                  placeholder="Additional notes..."
                  value={recordForm.notes}
                  onChange={(e) => setRecordForm({ ...recordForm, notes: e.target.value })}
                  className="input"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button onClick={() => setRecordModal(null)} className="btn-secondary flex-1">
                  Cancel
                </button>
                <button
                  onClick={handleCreateRecord}
                  disabled={actionLoading === 'record'}
                  className="btn-accent flex-1"
                >
                  {actionLoading === 'record' ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    'Save Record'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
