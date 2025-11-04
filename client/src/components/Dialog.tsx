import { X } from "lucide-react";

type AlertProps = {
  message: string;
  onClose: () => void;
};

export const Alert = ({ message, onClose }: AlertProps) => (
  <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50 p-4">
    <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 relative">
      <button
        onClick={onClose}
        className="absolute top-3 right-3 p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200"
      >
        <X className="w-5 h-5" />
      </button>
      <p className="text-slate-900 text-lg">{message}</p>
      <button
        onClick={onClose}
        className="mt-6 w-full bg-indigo-600 text-white py-2.5 rounded-lg font-medium hover:bg-indigo-700 transition-all duration-200"
      >
        OK
      </button>
    </div>
  </div>
);

type ConfirmProps = {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
};

export const Confirm = ({ message, onConfirm, onCancel }: ConfirmProps) => (
  <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50 p-4">
    <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 relative">
      <button
        onClick={onCancel}
        className="absolute top-3 right-3 p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200"
      >
        <X className="w-5 h-5" />
      </button>
      <p className="text-slate-900 text-lg">{message}</p>
      <div className="mt-6 flex gap-4">
        <button
          onClick={onCancel}
          className="flex-1 bg-slate-100 text-slate-700 py-2.5 rounded-lg font-medium hover:bg-slate-200 transition-all duration-200"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          className="flex-1 bg-indigo-600 text-white py-2.5 rounded-lg font-medium hover:bg-indigo-700 transition-all duration-200"
        >
          Confirm
        </button>
      </div>
    </div>
  </div>
);
