import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';
import {
  Stethoscope,
  Star,
  Clock,
  Calendar,
  CheckCircle,
  ArrowLeft,
  Send,
  Award,
  DollarSign,
} from 'lucide-react';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function DoctorDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, role } = useAuth();

  const [doctor, setDoctor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [reason, setReason] = useState('');
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    const fetchDoctor = async () => {
      try {
        const { data } = await api.get(`/doctors/${id}/`);
        setDoctor(data);
      } catch {
        toast.error('Doctor not found');
        navigate('/doctors');
      } finally {
        setLoading(false);
      }
    };
    fetchDoctor();
  }, [id, navigate]);

  // Group slots by day
  const slotsByDay = {};
  if (doctor?.availability_slots) {
    doctor.availability_slots.forEach((slot) => {
      if (!slot.is_active) return;
      const day = slot.day_of_week;
      if (!slotsByDay[day]) slotsByDay[day] = [];
      slotsByDay[day].push(slot);
    });
  }

  // Calculate valid dates for selected slot
  const getMinDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 1); // tomorrow
    return d.toISOString().split('T')[0];
  };

  const handleBook = async () => {
    if (!selectedSlot || !selectedDate) {
      toast.error('Please select a slot and date');
      return;
    }
    if (!isAuthenticated) {
      toast.error('Please log in to book an appointment');
      navigate('/login');
      return;
    }
    if (role !== 'PATIENT') {
      toast.error('Only patients can book appointments');
      return;
    }

    setBooking(true);
    try {
      await api.post('/appointments/', {
        slot: selectedSlot.id,
        date: selectedDate,
        reason,
      });
      toast.success('Appointment booked successfully!');
      navigate('/appointments');
    } catch (err) {
      const msg = err.response?.data?.detail ||
        Object.values(err.response?.data || {}).flat().join(' ') ||
        'Failed to book appointment';
      toast.error(msg);
    } finally {
      setBooking(false);
    }
  };

  if (loading) return <LoadingSpinner size="lg" className="py-32" />;
  if (!doctor) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Back button */}
      <button
        onClick={() => navigate('/doctors')}
        className="btn-ghost mb-6 -ml-2 text-sm"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Doctors
      </button>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Doctor Info — Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Profile Card */}
          <div className="card p-8">
            <div className="flex items-start gap-6">
              <div className="w-20 h-20 rounded-2xl gradient-primary flex items-center justify-center shadow-lg shadow-primary-500/20 shrink-0">
                <span className="text-2xl font-bold text-white">
                  {(doctor.full_name || 'D')[0].toUpperCase()}
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold text-gray-900">
                    Dr. {doctor.full_name}
                  </h1>
                  {doctor.is_verified && (
                    <CheckCircle className="w-5 h-5 text-accent-500" />
                  )}
                </div>
                <p className="text-primary-600 font-medium mt-1">
                  {doctor.specialty?.name || 'General Medicine'}
                </p>
                <p className="text-sm text-gray-500 mt-1">{doctor.email}</p>

                <div className="flex items-center gap-6 mt-4">
                  <div className="flex items-center gap-1.5 text-sm text-gray-600">
                    <Award className="w-4 h-4 text-amber-500" />
                    <span>{doctor.experience_years} years experience</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-sm text-gray-600">
                    <DollarSign className="w-4 h-4 text-green-500" />
                    <span>₹{doctor.fee} consultation</span>
                  </div>
                </div>
              </div>
            </div>

            {doctor.bio && (
              <div className="mt-6 pt-6 border-t border-gray-100">
                <h3 className="text-sm font-semibold text-gray-900 mb-2">About</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{doctor.bio}</p>
              </div>
            )}
          </div>

          {/* Availability Slots */}
          <div className="card p-8">
            <h2 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary-600" />
              Available Slots
            </h2>

            {Object.keys(slotsByDay).length === 0 ? (
              <p className="text-gray-400 text-center py-8">
                No availability slots configured yet.
              </p>
            ) : (
              <div className="space-y-4">
                {DAYS.map((dayName, idx) => {
                  const daySlots = slotsByDay[idx];
                  if (!daySlots) return null;
                  return (
                    <div key={idx}>
                      <p className="text-sm font-semibold text-gray-700 mb-2">{dayName}</p>
                      <div className="flex flex-wrap gap-2">
                        {daySlots.map((slot) => (
                          <button
                            key={slot.id}
                            onClick={() => {
                              setSelectedSlot(slot);
                              setSelectedDate('');
                            }}
                            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
                              selectedSlot?.id === slot.id
                                ? 'bg-primary-600 text-white border-primary-600 shadow-md shadow-primary-500/20'
                                : 'bg-white text-gray-700 border-gray-200 hover:border-primary-300 hover:bg-primary-50'
                            }`}
                          >
                            {slot.start_time?.slice(0, 5)} – {slot.end_time?.slice(0, 5)}
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Booking Panel — Right Column */}
        <div>
          <div className="card p-6 sticky top-24">
            <h2 className="text-lg font-bold text-gray-900 mb-1 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-primary-600" />
              Book Appointment
            </h2>
            <p className="text-sm text-gray-400 mb-6">
              Select a time slot and pick a date
            </p>

            {selectedSlot ? (
              <div className="space-y-4">
                <div className="p-3 bg-primary-50 rounded-xl border border-primary-100">
                  <p className="text-sm font-medium text-primary-700">
                    {DAYS[selectedSlot.day_of_week]} · {selectedSlot.start_time?.slice(0, 5)} – {selectedSlot.end_time?.slice(0, 5)}
                  </p>
                </div>

                <div>
                  <label htmlFor="appt-date" className="label">Date</label>
                  <input
                    id="appt-date"
                    type="date"
                    min={getMinDate()}
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="input"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Pick a {DAYS[selectedSlot.day_of_week]}
                  </p>
                </div>

                <div>
                  <label htmlFor="appt-reason" className="label">Reason (optional)</label>
                  <textarea
                    id="appt-reason"
                    rows={3}
                    placeholder="Describe your symptoms..."
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="input"
                  />
                </div>

                <button
                  id="book-appointment-btn"
                  onClick={handleBook}
                  disabled={!selectedDate || booking}
                  className="btn-primary w-full py-3"
                >
                  {booking ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Confirm Booking
                    </>
                  )}
                </button>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <Calendar className="w-10 h-10 mx-auto mb-3 opacity-40" />
                <p className="text-sm">Select a time slot to continue</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
