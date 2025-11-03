import { useEffect, useState } from 'react'
import type { Dashboard } from '../types/dashboard'
import { Link2 } from 'lucide-react'
import { api } from '../services/TzHarApi'

export default function DashboardPage() {

    const [dashboard, setDashboard] = useState<Dashboard | null>(null)

    const init = async () => {
        const data = await api.dashboard.getDashboard();
        setDashboard(data);
    }

    useEffect(() => {
        init()
    }, [])

    if (!dashboard) { return <></>}

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-900">Dashboard</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
                    <Link2 className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div>
                    <p className="text-sm text-slate-600">Total URLs</p>
                    <p className="text-2xl font-bold text-slate-900">{dashboard.total_urls}</p>
                    </div>
                </div>
                </div>
                
            </div>
        </div>
    )
}
