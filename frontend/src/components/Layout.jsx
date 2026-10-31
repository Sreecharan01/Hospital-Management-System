import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import { Stethoscope } from 'lucide-react';

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg gradient-primary flex items-center justify-center">
                <Stethoscope className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-gray-700">MedConnect</span>
            </div>
            <p className="text-sm text-gray-400">
              © {new Date().getFullYear()} MedConnect. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
