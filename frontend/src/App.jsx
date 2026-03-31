import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import ChildHome from './pages/child/ChildHome.jsx'
import MissionPage from './pages/child/MissionPage.jsx'
import AnswerPage from './pages/child/AnswerPage.jsx'
import ResultPage from './pages/child/ResultPage.jsx'
import ParentLayout from './pages/parent/ParentLayout.jsx'
import OverviewPage from './pages/parent/OverviewPage.jsx'
import WrongQuestionsPage from './pages/parent/WrongQuestionsPage.jsx'
import WeeklyReportPage from './pages/parent/WeeklyReportPage.jsx'
import QuestionsPage from './pages/parent/QuestionsPage.jsx'

function RequireAuth({ children }) {
  const token = localStorage.getItem('token')
  if (!token) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        {/* 孩子端 */}
        <Route path="/child/:childId/home" element={<RequireAuth><ChildHome /></RequireAuth>} />
        <Route path="/child/:childId/mission" element={<RequireAuth><MissionPage /></RequireAuth>} />
        <Route path="/child/:childId/answer" element={<RequireAuth><AnswerPage /></RequireAuth>} />
        <Route path="/child/:childId/result" element={<RequireAuth><ResultPage /></RequireAuth>} />

        {/* 家长端 */}
        <Route path="/parent" element={<RequireAuth><ParentLayout /></RequireAuth>}>
          <Route index element={<Navigate to="overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="wrong-questions" element={<WrongQuestionsPage />} />
          <Route path="weekly" element={<WeeklyReportPage />} />
          <Route path="questions" element={<QuestionsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
