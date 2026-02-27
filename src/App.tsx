import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Stats from "./pages/Stats";
import CourseDetail from "./pages/CourseDetail";
import NotFound from "./pages/NotFound";

// basic route map
function App() {
  function navClassName({ isActive }: { isActive: boolean }) {
    return isActive ? "active" : "";
  }

  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="site-header">
          <div>
            <h1>Course Review Site</h1>
            <p>browse classes, ratings, and student feedback.</p>
          </div>
          <nav className="site-nav">
            <NavLink to="/" end className={navClassName}>
              home
            </NavLink>
            <NavLink to="/login" className={navClassName}>
              login
            </NavLink>
            <NavLink to="/stats" className={navClassName}>
              stats
            </NavLink>
            <NavLink to="/course/101" className={navClassName}>
              sample course
            </NavLink>
          </nav>
        </header>

        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/login" element={<Login />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/course/:courseid" element={<CourseDetail />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
