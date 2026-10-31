import { useState, useEffect } from 'react';
import api from '../api/axios';
import LoadingSpinner from '../components/LoadingSpinner';
import StatusBadge from '../components/StatusBadge';
import toast from 'react-hot-toast';
import {
  Calendar,
  Clock,
  XCircle,
  RefreshCw,
  Stethoscope,
  X,
} from 'lucide-react';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function MyAppointments() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('upcoming');
  const [rescheduleModal, setRescheduleModal] = useState(null);
  const [rescheduleData, setRescheduleData] = useState({ slot: '', date: '', appointment_time: '' });
  const [availableSlots, setAvailableSlots] = useState([]);
  const [rescheduleTimeSlots, setRescheduleTimeSlots] = useState([]);
  const [loadingTimes, setLoadingTimes] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  const fetchAppointments = async () => {
    try {
      const { data } = await api.get('/appointments/');
      setAppointments(data.results || data);
    } catch {
      toast.error('Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const today = new Date().toISOString().split('T')[0];
  const upcoming = appointments.filter(
    (a) => a.date >= today && !['CANCELLED', 'COMPLETED', 'EXPIRED'].includes(a.status)
  );
  const past = appointments.filter(
    (a) => a.date < today || ['CANCELLED', 'COMPLETED', 'EXPIRED'].includes(a.status)
  );
  const displayed = tab === 'upcoming' ? upcoming : past;

  const handleCancel = async (id) => {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    setActionLoading(id);
    try {
      await api.post(`/appointments/${id}/cancel/`);
      toast.success('Appointment cancelled');
      fetchAppointments();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to cancel');
    } finally {
      setActionLoading(null);
    }
  };

  const openReschedule = async (appt) => {
    setRescheduleModal(appt);
    setRescheduleData({ slot: '', date: '', appointment_time: '' });
    setRescheduleTimeSlots([]);
    try {
      const doctorId = appt.slot?.doctor?.id;
      if (doctorId) {
        const { data } = await api.get(`/doctors/${doctorId}/slots/`);
        setAvailableSlots(data.results || data);
      }
    } catch {
      setAvailableSlots([]);
    }
  };

  // Fetch available times when reschedule slot + date change
  useEffect(() => {
    if (!rescheduleData.slot || !rescheduleData.date) {
      setRescheduleTimeSlots([]);
      return;
    }
    const fetchTimes = async () => {
      setLoadingTimes(true);
      setRescheduleData((prev) => ({ ...prev, appointment_time: '' }));
      try {
        const { data } = await api.get('/appointments/available-times/', {
          params: { slot: rescheduleData.slot, date: rescheduleData.date },
        });
        setRescheduleTimeSlots(data.times || []);
      } catch {
        setRescheduleTimeSlots([]);
      } finally {
        setLoadingTimes(false);
      }
    };
    fetchTimes();
  }, [rescheduleData.slot, rescheduleData.date]);

  const handleReschedule = async () => {
    if (!rescheduleData.slot || !rescheduleData.date || !rescheduleData.appointment_time) {
      toast.error('Select a slot, date, and time');
      return;
    }
    setActionLoading(rescheduleModal.id);
    try {
      await api.post(`/appointments/${rescheduleModal.id}/reschedule/`, {
        slot: rescheduleData.slot,
        date: rescheduleData.date,
        appointment_time: rescheduleData.appointment_time,
      });
      toast.success('Appointment rescheduled');
      setRescheduleModal(null);
      fetchAppointments();
    } catch (err) {
      toast.error(err.response?.data?.detail || Object.values(err.response?.data || {}).flat().join(' ') || 'Failed to reschedule');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return <LoadingSpinner size="lg" className="py-32" />;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">My Appointments</h1>
      <p className="text-gray-500 mb-8">Manage your scheduled appointments</p>

      {/* Tabs */}
      <div className="flex rounded-xl bg-gray-100 p-1 mb-8 max-w-xs">
        {['upcoming', 'past'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all capitalize ${
              tab === t
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t} ({t === 'upcoming' ? upcoming.length : past.length})
          </button>
        ))}
      </div>

      {/* Appointments list */}
      {displayed.length === 0 ? (
        <div className="text-center py-20">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-500">
            No {tab} appointments
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayed.map((appt) => {
            const doctorName = appt.slot?.doctor?.full_name || '';
            const specialty = appt.slot?.doctor?.specialty?.name || '';
            return (
              <div
                key={appt.id}
                className="card p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Stethoscope className="w-4 h-4 text-primary-500 shrink-0" />
                      <p className="font-semibold text-gray-900">
                        Dr. {doctorName}
                      </p>
                      <StatusBadge status={appt.status} />
                    </div>
                    {specialty && (
                      <p className="text-xs text-gray-400 mt-0.5 ml-6">{specialty}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
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
                      <p className="text-xs text-gray-400 mt-2 line-clamp-1">
                        Reason: {appt.reason}
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  {tab === 'upcoming' && (
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => openReschedule(appt)}
                        disabled={actionLoading === appt.id}
                        className="btn-secondary btn-sm text-xs"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                        Reschedule
                      </button>
                      <button
                        onClick={() => handleCancel(appt.id)}
                        disabled={actionLoading === appt.id}
                        className="btn-danger btn-sm text-xs"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Reschedule Modal */}
      {rescheduleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale-in">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-gray-900">Reschedule Appointment</h3>
              <button onClick={() => setRescheduleModal(null)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Select Slot</label>
                <select
                  value={rescheduleData.slot}
                  onChange={(e) => setRescheduleData({ ...rescheduleData, slot: e.target.value, date: '', appointment_time: '' })}
                  className="input"
                >
                  <option value="">Choose a slot</option>
                  {availableSlots.filter(s => s.is_active).map((s) => (
                    <option key={s.id} value={s.id}>
                      {DAYS[s.day_of_week]} · {s.start_time?.slice(0, 5)} – {s.end_time?.slice(0, 5)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">New Date</label>
                <input
                  type="date"
                  min={new Date(Date.now() + 86400000).toISOString().split('T')[0]}
                  value={rescheduleData.date}
                  onChange={(e) => setRescheduleData({ ...rescheduleData, date: e.target.value, appointment_time: '' })}
                  className="input"
                />
              </div>

              {/* Time slots */}
              {rescheduleData.slot && rescheduleData.date && (
                <div>
                  <label className="label">Select Time</label>
                  {loadingTimes ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="w-5 h-5 border-2 border-primary-300 border-t-primary-600 rounded-full animate-spin" />
                    </div>
                  ) : rescheduleTimeSlots.length === 0 ? (
                    <p className="text-sm text-gray-400 text-center py-3">No times available</p>
                  ) : (
                    <div className="grid grid-cols-4 gap-2">
                      {rescheduleTimeSlots.map((ts) => (
                        <button
                          key={ts.time}
                          type="button"
                          onClick={() => {
                            if (ts.available) setRescheduleData({ ...rescheduleData, appointment_time: ts.time });
                          }}
                          disabled={!ts.available}
                          className={`px-2 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                            !ts.available
                              ? 'bg-red-50 text-red-300 border-red-100 cursor-not-allowed line-through'
                              : rescheduleData.appointment_time === ts.time
                              ? 'bg-primary-600 text-white border-primary-600'
                              : 'bg-white text-gray-700 border-gray-200 hover:border-primary-300'
                          }`}
                        >
                          {ts.time}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setRescheduleModal(null)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReschedule}
                  disabled={actionLoading || !rescheduleData.appointment_time}
                  className="btn-primary flex-1"
                >
                  {actionLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    'Reschedule'
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
