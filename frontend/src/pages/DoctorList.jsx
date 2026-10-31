import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/axios';
import LoadingSpinner from '../components/LoadingSpinner';
import { Search, Filter, Star, MapPin, ArrowRight, Stethoscope } from 'lucide-react';

export default function DoctorList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [doctors, setDoctors] = useState([]);
  const [specialties, setSpecialties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [specialtyFilter, setSpecialtyFilter] = useState(searchParams.get('specialty') || '');

  const fetchDoctors = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (specialtyFilter) params.specialty = specialtyFilter;
      const { data } = await api.get('/doctors/', { params });
      setDoctors(data.results || data);
    } catch {
      setDoctors([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api.get('/specialties/').then((r) => setSpecialties(r.data.results || r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    const timeout = setTimeout(fetchDoctors, 300);
    return () => clearTimeout(timeout);
  }, [search, specialtyFilter]);

  const handleSearch = (val) => {
    setSearch(val);
    const params = {};
    if (val) params.search = val;
    if (specialtyFilter) params.specialty = specialtyFilter;
    setSearchParams(params);
  };

  const handleSpecialty = (val) => {
    setSpecialtyFilter(val);
    const params = {};
    if (search) params.search = search;
    if (val) params.specialty = val;
    setSearchParams(params);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Find a Doctor</h1>
        <p className="text-gray-500 mt-1">Browse our verified medical specialists</p>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-8">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              id="doctor-search"
              type="text"
              placeholder="Search by name..."
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <div className="sm:w-64 relative">
            <Filter className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              id="specialty-filter"
              value={specialtyFilter}
              onChange={(e) => handleSpecialty(e.target.value)}
              className="input pl-10"
            >
              <option value="">All Specialties</option>
              {specialties.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <LoadingSpinner size="lg" className="py-20" />
      ) : doctors.length === 0 ? (
        <div className="text-center py-20">
          <Stethoscope className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-500">No doctors found</p>
          <p className="text-sm text-gray-400 mt-1">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctors.map((doc) => (
            <Link
              key={doc.id}
              to={`/doctors/${doc.id}`}
              className="card-hover p-6 group"
            >
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-2xl gradient-primary flex items-center justify-center shrink-0 shadow-lg shadow-primary-500/15 group-hover:shadow-xl transition-shadow">
                  <span className="text-lg font-bold text-white">
                    {(doc.full_name || 'D')[0].toUpperCase()}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                    Dr. {doc.full_name}
                  </h3>
                  <p className="text-sm text-primary-600 font-medium mt-0.5">
                    {doc.specialty?.name || 'General Medicine'}
                  </p>
                </div>
              </div>

              {doc.bio && (
                <p className="text-sm text-gray-500 mt-4 line-clamp-2">{doc.bio}</p>
              )}

              <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Star className="w-3.5 h-3.5 text-amber-400" />
                    {doc.experience_years}y
                  </span>
                  <span className="font-medium text-gray-700">₹{doc.fee}</span>
                </div>
                <span className="text-primary-600 group-hover:translate-x-1 transition-transform">
                  <ArrowRight className="w-4 h-4" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
