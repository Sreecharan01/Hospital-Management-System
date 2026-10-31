import { useState, useEffect } from 'react';
import api from '../api/axios';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  Users,
  Stethoscope,
  Calendar,
  FileText,
  Shield,
  CheckCircle,
  Plus,
  Trash2,
  Send,
  Activity,
  Bell,
  TrendingUp,
  X,
} from 'lucide-react';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [doctors, setDoctors] = useState([]);
  const [specialties, setSpecialties] = useState([]);
  const [loading, setLoading] = useState(true);

  // Specialty form
  const [newSpecialty, setNewSpecialty] = useState({ name: '', description: '' });
  const [addingSpec, setAddingSpec] = useState(false);

  // Announcement form
  const [announcement, setAnnouncement] = useState({ title: '', message: '', roles: ['PATIENT', 'DOCTOR'] });
  const [sending, setSending] = useState(false);

  const [actionLoading, setActionLoading] = useState(null);

  const fetchAll = async () => {
    try {
      const [statsRes, docsRes, specsRes] = await Promise.all([
        api.get('/admin/stats/'),
        api.get('/doctors/'),
        api.get('/specialties/'),
      ]);
      setStats(statsRes.data);
      setDoctors(docsRes.data.results || docsRes.data);
      setSpecialties(specsRes.data.results || specsRes.data);
    } catch {
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  // Verify doctor
  const verifyDoctor = async (docId) => {
    setActionLoading(docId);
    try {
      await api.post(`/doctors/${docId}/verify/`);
      toast.success('Doctor verified');
      fetchAll();
    } catch {
      toast.error('Failed to verify doctor');
    } finally {
      setActionLoading(null);
    }
  };

  // Add specialty
  const handleAddSpecialty = async (e) => {
    e.preventDefault();
    if (!newSpecialty.name.trim()) return;
    setAddingSpec(true);
    try {
      await api.post('/specialties/', newSpecialty);
      toast.success('Specialty added');
      setNewSpecialty({ name: '', description: '' });
      fetchAll();
    } catch (err) {
      toast.error(err.response?.data?.name?.[0] || 'Failed to add specialty');
    } finally {
      setAddingSpec(false);
    }
  };

  const deleteSpecialty = async (id) => {
    if (!confirm('Delete this specialty?')) return;
    try {
      await api.delete(`/specialties/${id}/`);
      toast.success('Specialty deleted');
      fetchAll();
    } catch {
      toast.error('Failed to delete specialty');
    }
  };

  // Send announcement
  const handleAnnounce = async (e) => {
    e.preventDefault();
    if (!announcement.title.trim() || !announcement.message.trim()) {
      toast.error('Title and message are required');
      return;
    }
    setSending(true);
    try {
      const { data } = await api.post('/admin/announce/', announcement);
      toast.success(`Announcement sent to ${data.notified_users} users`);
      setAnnouncement({ title: '', message: '', roles: ['PATIENT', 'DOCTOR'] });
    } catch {
      toast.error('Failed to send announcement');
    } finally {
      setSending(false);
    }
  };

  const toggleRole = (role) => {
    setAnnouncement((prev) => ({
      ...prev,
      roles: prev.roles.includes(role)
        ? prev.roles.filter((r) => r !== role)
        : [...prev.roles, role],
    }));
  };

  if (loading) return <LoadingSpinner size="lg" className="py-32" />;

  const unverifiedDocs = doctors.filter((d) => !d.is_verified);

  // Stat cards data
  const statCards = [
    { label: 'Total Users', value: stats?.users?.total || 0, icon: Users, color: 'from-blue-500 to-blue-600', bg: 'bg-blue-50' },
    { label: 'Patients', value: stats?.users?.patients || 0, icon: Users, color: 'from-green-500 to-green-600', bg: 'bg-green-50' },
    { label: 'Doctors', value: stats?.users?.doctors || 0, icon: Stethoscope, color: 'from-purple-500 to-purple-600', bg: 'bg-purple-50' },
    { label: 'Appointments', value: stats?.appointments?.total || 0, icon: Calendar, color: 'from-amber-500 to-amber-600', bg: 'bg-amber-50' },
    { label: 'Pending Verification', value: stats?.doctors?.pending_verification || 0, icon: Shield, color: 'from-red-500 to-red-600', bg: 'bg-red-50' },
    { label: 'Medical Records', value: stats?.medical_records || 0, icon: FileText, color: 'from-teal-500 to-teal-600', bg: 'bg-teal-50' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-500 mt-1">System overview and management</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {statCards.map((s) => (
          <div key={s.label} className="card p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 font-medium">{s.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{s.value}</p>
              </div>
              <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${s.color} flex items-center justify-center shadow-lg`}>
                <s.icon className="w-5 h-5 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Chart */}
      {stats?.appointments_per_day?.length > 0 && (
        <div className="card p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-600" />
            Appointments (Last 30 Days)
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.appointments_per_day}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  tickFormatter={(d) => d.slice(5)}
                />
                <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    borderRadius: '12px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fill="url(#colorCount)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Doctor Verification */}
        <div className="card p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary-600" />
            Doctor Verification ({unverifiedDocs.length})
          </h2>

          {unverifiedDocs.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="text-sm">All doctors verified</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {unverifiedDocs.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900 text-sm truncate">
                      Dr. {doc.full_name}
                    </p>
                    <p className="text-xs text-gray-500">{doc.specialty?.name || 'N/A'} · {doc.email}</p>
                  </div>
                  <button
                    onClick={() => verifyDoctor(doc.id)}
                    disabled={actionLoading === doc.id}
                    className="btn-sm bg-green-50 text-green-700 border border-green-200 rounded-lg hover:bg-green-100 inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 shrink-0 ml-3 transition-colors"
                  >
                    {actionLoading === doc.id ? (
                      <div className="w-3.5 h-3.5 border-2 border-green-300 border-t-green-700 rounded-full animate-spin" />
                    ) : (
                      <>
                        <CheckCircle className="w-3.5 h-3.5" />
                        Verify
                      </>
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Specialties Manager */}
        <div className="card p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary-600" />
            Specialties ({specialties.length})
          </h2>

          <form onSubmit={handleAddSpecialty} className="flex gap-2 mb-4">
            <input
              placeholder="Specialty name"
              value={newSpecialty.name}
              onChange={(e) => setNewSpecialty({ ...newSpecialty, name: e.target.value })}
              className="input flex-1"
            />
            <button type="submit" disabled={addingSpec} className="btn-primary btn-sm shrink-0">
              <Plus className="w-4 h-4" />
            </button>
          </form>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {specialties.map((s) => (
              <div key={s.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                <div>
                  <p className="text-sm font-medium text-gray-900">{s.name}</p>
                  {s.description && (
                    <p className="text-xs text-gray-400 truncate max-w-[200px]">{s.description}</p>
                  )}
                </div>
                <button
                  onClick={() => deleteSpecialty(s.id)}
                  className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Announcements */}
        <div className="card p-6 lg:col-span-2">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5 text-primary-600" />
            Send Announcement
          </h2>

          <form onSubmit={handleAnnounce} className="space-y-4">
            <div>
              <label className="label">Title</label>
              <input
                placeholder="Announcement title"
                value={announcement.title}
                onChange={(e) => setAnnouncement({ ...announcement, title: e.target.value })}
                className="input"
              />
            </div>
            <div>
              <label className="label">Message</label>
              <textarea
                rows={3}
                placeholder="Write your announcement..."
                value={announcement.message}
                onChange={(e) => setAnnouncement({ ...announcement, message: e.target.value })}
                className="input"
              />
            </div>
            <div>
              <label className="label">Target Roles</label>
              <div className="flex gap-3">
                {['PATIENT', 'DOCTOR', 'ADMIN'].map((r) => (
                  <label key={r} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={announcement.roles.includes(r)}
                      onChange={() => toggleRole(r)}
                      className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700 capitalize">{r.toLowerCase()}</span>
                  </label>
                ))}
              </div>
            </div>
            <button type="submit" disabled={sending} className="btn-primary">
              {sending ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Send Announcement
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
