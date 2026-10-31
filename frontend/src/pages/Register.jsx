import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';
import {
  UserPlus,
  Mail,
  Lock,
  User,
  Stethoscope,
  AlertCircle,
  Briefcase,
  Heart,
} from 'lucide-react';
import toast from 'react-hot-toast';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [role, setRole] = useState('PATIENT');
  const [specialties, setSpecialties] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    // Patient fields
    dob: '',
    phone: '',
    address: '',
    blood_group: '',
    // Doctor fields
    specialty_id: '',
    bio: '',
    fee: '',
    experience_years: '',
  });

  useEffect(() => {
    api.get('/specialties/').then((r) => setSpecialties(r.data.results || r.data)).catch(() => {});
  }, []);

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
        role,
      };

      if (role === 'PATIENT') {
        if (form.dob) payload.dob = form.dob;
        if (form.phone) payload.phone = form.phone;
        if (form.address) payload.address = form.address;
        if (form.blood_group) payload.blood_group = form.blood_group;
      } else {
        if (form.specialty_id) payload.specialty_id = form.specialty_id;
        if (form.bio) payload.bio = form.bio;
        if (form.fee) payload.fee = form.fee;
        if (form.experience_years) payload.experience_years = parseInt(form.experience_years, 10);
      }

      await register(payload);
      navigate('/login');
    } catch (err) {
      const data = err.response?.data;
      let msg = 'Registration failed. Please check your inputs.';
      if (typeof data === 'object') {
        const first = Object.values(data).flat()[0];
        if (typeof first === 'string') msg = first;
        else if (first?.message) msg = first.message;
      }
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4">
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-100 rounded-full blur-3xl opacity-50" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-accent-100 rounded-full blur-3xl opacity-50" />
      </div>

      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl gradient-primary shadow-lg shadow-primary-500/20 mb-4">
            <Stethoscope className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Create an account</h1>
          <p className="text-gray-500 mt-1">Join MedConnect today</p>
        </div>

        <div className="card p-8">
          {/* Role selector */}
          <div className="flex rounded-xl bg-gray-100 p-1 mb-6">
            <button
              type="button"
              onClick={() => setRole('PATIENT')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                role === 'PATIENT'
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Heart className="w-4 h-4" />
              Patient
            </button>
            <button
              type="button"
              onClick={() => setRole('DOCTOR')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                role === 'DOCTOR'
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              Doctor
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 mb-6 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Common fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="label">First name</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input id="first_name" required placeholder="John" value={form.first_name} onChange={set('first_name')} className="input pl-10" />
                </div>
              </div>
              <div>
                <label htmlFor="last_name" className="label">Last name</label>
                <input id="last_name" required placeholder="Doe" value={form.last_name} onChange={set('last_name')} className="input" />
              </div>
            </div>

            <div>
              <label htmlFor="reg-email" className="label">Email</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input id="reg-email" type="email" required placeholder="you@example.com" value={form.email} onChange={set('email')} className="input pl-10" />
              </div>
            </div>

            <div>
              <label htmlFor="reg-password" className="label">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input id="reg-password" type="password" required minLength={8} placeholder="Min 8 characters" value={form.password} onChange={set('password')} className="input pl-10" />
              </div>
            </div>

            {/* Patient-specific fields */}
            {role === 'PATIENT' && (
              <div className="space-y-4 pt-2 border-t border-gray-100">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider pt-2">Patient Details</p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="dob" className="label">Date of Birth</label>
                    <input id="dob" type="date" value={form.dob} onChange={set('dob')} className="input" />
                  </div>
                  <div>
                    <label htmlFor="phone" className="label">Phone</label>
                    <input id="phone" type="tel" placeholder="+91 ..." value={form.phone} onChange={set('phone')} className="input" />
                  </div>
                </div>
                <div>
                  <label htmlFor="blood_group" className="label">Blood Group</label>
                  <select id="blood_group" value={form.blood_group} onChange={set('blood_group')} className="input">
                    <option value="">Select (optional)</option>
                    {BLOOD_GROUPS.map((bg) => (
                      <option key={bg} value={bg}>{bg}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="address" className="label">Address</label>
                  <textarea id="address" rows={2} placeholder="Your address" value={form.address} onChange={set('address')} className="input" />
                </div>
              </div>
            )}

            {/* Doctor-specific fields */}
            {role === 'DOCTOR' && (
              <div className="space-y-4 pt-2 border-t border-gray-100">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider pt-2">Professional Details</p>
                <div>
                  <label htmlFor="specialty_id" className="label">Specialty</label>
                  <select id="specialty_id" value={form.specialty_id} onChange={set('specialty_id')} className="input">
                    <option value="">Select specialty</option>
                    {specialties.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="fee" className="label">Consultation Fee (₹)</label>
                    <input id="fee" type="number" min={0} step="0.01" placeholder="500" value={form.fee} onChange={set('fee')} className="input" />
                  </div>
                  <div>
                    <label htmlFor="experience_years" className="label">Experience (years)</label>
                    <input id="experience_years" type="number" min={0} placeholder="5" value={form.experience_years} onChange={set('experience_years')} className="input" />
                  </div>
                </div>
                <div>
                  <label htmlFor="bio" className="label">Bio</label>
                  <textarea id="bio" rows={3} placeholder="Tell patients about yourself..." value={form.bio} onChange={set('bio')} className="input" />
                </div>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full py-3 mt-2" id="register-submit">
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Create Account
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-700">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
