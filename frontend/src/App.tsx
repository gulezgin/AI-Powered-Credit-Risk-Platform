import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ControlCenter from "./pages/ControlCenter";
import Customer360 from "./pages/Customer360";
import EarlyWarningAlerts from "./pages/EarlyWarningAlerts";
import ModelMonitoring from "./pages/ModelMonitoring";
import LiveRiskSimulator from "./pages/LiveRiskSimulator";
import StressTestLab from "./pages/StressTestLab";
import RealDataset from "./pages/RealDataset";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<ControlCenter />} />
          <Route path="customer" element={<Customer360 />} />
          <Route path="alerts" element={<EarlyWarningAlerts />} />
          <Route path="monitoring" element={<ModelMonitoring />} />
          <Route path="simulator" element={<LiveRiskSimulator />} />
          <Route path="stress-test" element={<StressTestLab />} />
          <Route path="real-dataset" element={<RealDataset />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
