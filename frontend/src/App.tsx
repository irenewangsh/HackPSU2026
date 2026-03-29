import { Route, Routes } from "react-router-dom";
import { Shell } from "./layout/Shell";
import { IntroPage } from "./pages/IntroPage";
import { Dashboard } from "./pages/Dashboard";
import { MediationPage } from "./pages/MediationPage";
import { HooksPage } from "./pages/HooksPage";
import { HeatmapPage } from "./pages/HeatmapPage";
import { TimelinePage } from "./pages/TimelinePage";
import { OperationsPage } from "./pages/OperationsPage";
import { ProfilePage } from "./pages/ProfilePage";
import { DemoPage } from "./pages/DemoPage";
import { DevpostPage } from "./pages/DevpostPage";
import { AuditPage } from "./pages/AuditPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<IntroPage />} />
      <Route element={<Shell />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="mediate" element={<MediationPage />} />
        <Route path="hooks" element={<HooksPage />} />
        <Route path="heatmap" element={<HeatmapPage />} />
        <Route path="timeline" element={<TimelinePage />} />
        <Route path="operations" element={<OperationsPage />} />
        <Route path="audit" element={<AuditPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="demo" element={<DemoPage />} />
        <Route path="devpost" element={<DevpostPage />} />
      </Route>
    </Routes>
  );
}
