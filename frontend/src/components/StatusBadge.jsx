const STATUS_CONFIG = {
  PENDING:   { label: 'Pending',   bg: 'bg-amber-50',   text: 'text-amber-700',  dot: 'bg-amber-500' },
  CONFIRMED: { label: 'Confirmed', bg: 'bg-blue-50',    text: 'text-blue-700',   dot: 'bg-blue-500' },
  COMPLETED: { label: 'Attended',  bg: 'bg-green-50',   text: 'text-green-700',  dot: 'bg-green-500' },
  CANCELLED: { label: 'Cancelled', bg: 'bg-red-50',     text: 'text-red-700',    dot: 'bg-red-500' },
  EXPIRED:   { label: 'Expired',   bg: 'bg-gray-100',   text: 'text-gray-700',   dot: 'bg-gray-500' },
};

export default function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.PENDING;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${config.bg} ${config.text}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
}
