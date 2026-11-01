import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import { ErrorPanel } from "../components/ErrorPanel";
import { OptimizerPage } from "../pages/OptimizerPage";
import { PlannerPage } from "../pages/PlannerPage";

export function App() {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <h1>Gestion Satisfactory</h1>
        <p>Industrial planner + optimizer</p>
        <nav>
          <NavLink to="/planner" className={({ isActive }) => (isActive ? "active" : "")}>
            Factory Planner
          </NavLink>
          <NavLink to="/optimizer" className={({ isActive }) => (isActive ? "active" : "")}>
            Recipe Optimizer
          </NavLink>
        </nav>
      </aside>

      <div className="app-content">
        <ErrorPanel />
        <Routes>
          <Route path="/planner" element={<PlannerPage />} />
          <Route path="/optimizer" element={<OptimizerPage />} />
          <Route path="*" element={<Navigate to="/planner" replace />} />
        </Routes>
      </div>
    </div>
  );
}
