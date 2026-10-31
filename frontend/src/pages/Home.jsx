import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Stethoscope,
  Calendar,
  Shield,
  ArrowRight,
  Star,
  Clock,
  Award,
  Heart,
  Users,
  Activity,
} from 'lucide-react';
import api from '../api/axios';

const FEATURES = [
  {
    icon: Calendar,
    title: 'Easy Booking',
    desc: 'Book appointments online with verified doctors in just a few clicks.',
  },
  {
    icon: Shield,
    title: 'Secure Records',
    desc: 'Your medical records are encrypted and accessible anytime.',
  },
  {
    icon: Clock,
    title: 'Smart Reminders',
    desc: 'Automated reminders ensure you never miss an appointment.',
  },
  {
    icon: Heart,
    title: 'Quality Care',
    desc: 'Access to verified healthcare professionals you can trust.',
  },
];

const STATS = [
  { icon: Users, value: '10,000+', label: 'Patients Served' },
  { icon: Stethoscope, value: '200+', label: 'Verified Doctors' },
  { icon: Activity, value: '50,000+', label: 'Appointments Booked' },
  { icon: Award, value: '98%', label: 'Satisfaction Rate' },
];

export default function Home() {
  const [specialties, setSpecialties] = useState([]);
  const [doctors, setDoctors] = useState([]);

  useEffect(() => {
    api.get('/specialties/').then((r) => setSpecialties((r.data.results || r.data).slice(0, 8))).catch(() => {});
    api.get('/doctors/').then((r) => setDoctors((r.data.results || r.data).slice(0, 4))).catch(() => {});
  }, []);

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden gradient-hero text-white">
        {/* Decorative circles */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute bottom-10 right-20 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white/10 rounded-full text-sm font-medium mb-6 backdrop-blur-sm border border-white/10">
              <Activity className="w-4 h-4 text-accent-300" />
              <span>Trusted Healthcare Platform</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight">
              Your Health,{' '}
              <span className="bg-gradient-to-r from-accent-300 to-accent-400 bg-clip-text text-transparent">
                Our Priority
              </span>
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-gray-300 leading-relaxed max-w-2xl">
              Book appointments with verified specialists, manage your medical records, and receive timely
              reminders — all from one seamless platform.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <Link
                to="/doctors"
                className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-primary-700 font-semibold rounded-xl hover:bg-gray-100 transition-all duration-200 shadow-lg shadow-black/10"
              >
                Find a Doctor
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center gap-2 px-8 py-3.5 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition-all duration-200 border border-white/20 backdrop-blur-sm"
              >
                Create Account
              </Link>
            </div>
          </div>
        </div>

        {/* Bottom wave */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 60" fill="none" className="w-full">
            <path
              d="M0 60V30C240 0 480 0 720 30C960 60 1200 60 1440 30V60H0Z"
              fill="rgb(249 250 251)"
            />
          </svg>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center animate-fade-in">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-primary-50 text-primary-600 mb-3">
                  <stat.icon className="w-6 h-6" />
                </div>
                <p className="text-2xl sm:text-3xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
              Why Choose <span className="text-primary-600">MedConnect</span>?
            </h2>
            <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">
              A modern platform designed for seamless healthcare management.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((f, i) => (
              <div
                key={f.title}
                className="card-hover p-6 text-center"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 text-white mb-4 shadow-lg shadow-primary-500/20">
                  <f.icon className="w-7 h-7" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Specialties */}
      {specialties.length > 0 && (
        <section className="py-20 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-10">
              <div>
                <h2 className="section-title">Our Specialties</h2>
                <p className="text-gray-500 mt-1">Browse doctors by specialty</p>
              </div>
              <Link
                to="/doctors"
                className="hidden sm:inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                View all doctors <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {specialties.map((s) => (
                <Link
                  key={s.id}
                  to={`/doctors?specialty=${s.id}`}
                  className="card-hover p-5 flex flex-col items-center text-center gap-3 group"
                >
                  <div className="w-12 h-12 rounded-2xl bg-accent-50 text-accent-600 flex items-center justify-center group-hover:bg-accent-100 transition-colors">
                    <Stethoscope className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 text-sm">{s.name}</p>
                    {s.description && (
                      <p className="text-xs text-gray-400 mt-1 line-clamp-2">{s.description}</p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Featured Doctors */}
      {doctors.length > 0 && (
        <section className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900">Featured Doctors</h2>
              <p className="text-gray-500 mt-2">Verified specialists ready to help you</p>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {doctors.map((doc) => (
                <Link
                  key={doc.id}
                  to={`/doctors/${doc.id}`}
                  className="card-hover p-6 text-center group"
                >
                  <div className="w-16 h-16 rounded-full gradient-primary mx-auto flex items-center justify-center mb-4 shadow-lg shadow-primary-500/20 group-hover:shadow-xl group-hover:shadow-primary-500/30 transition-shadow">
                    <span className="text-xl font-bold text-white">
                      {(doc.full_name || 'D')[0].toUpperCase()}
                    </span>
                  </div>
                  <h3 className="font-semibold text-gray-900">Dr. {doc.full_name}</h3>
                  <p className="text-sm text-primary-600 mt-1">
                    {doc.specialty?.name || 'General'}
                  </p>
                  <div className="flex items-center justify-center gap-3 mt-3 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Star className="w-3 h-3 text-amber-400" /> {doc.experience_years}y exp
                    </span>
                    <span>₹{doc.fee}</span>
                  </div>
                </Link>
              ))}
            </div>
            <div className="text-center mt-10">
              <Link to="/doctors" className="btn-primary">
                View All Doctors <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="py-20 gradient-hero text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSA2MCAwIEwgMCAwIDAgNjAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-50" />
        <div className="relative max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold">Ready to Get Started?</h2>
          <p className="mt-4 text-lg text-gray-300 max-w-2xl mx-auto">
            Join thousands of patients who trust MedConnect for their healthcare needs.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              to="/register"
              className="px-8 py-3.5 bg-white text-primary-700 font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-lg"
            >
              Create Free Account
            </Link>
            <Link
              to="/doctors"
              className="px-8 py-3.5 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition-all border border-white/20"
            >
              Browse Doctors
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
