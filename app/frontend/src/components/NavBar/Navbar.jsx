import './Navbar.css';
import logo from '../../assets/light-logo-p.png';
import darkLogo from '../../assets/dark-logo-P.png';
import { NavLink, useNavigate } from 'react-router-dom'
import { getToken, logout } from '../../lib/api';

function Navbar({ darkMode, setDarkMode}){
    const navigate = useNavigate();
    // Navbar re-renders on every route change, so this stays current after login/logout.
    const isLoggedIn = Boolean(getToken());

    async function handleLogout() {
        await logout().catch(() => {});
        navigate('/login');
    }

    return (
        <nav className="navbar">
            <img src={darkMode ? darkLogo : logo} alt="CareerGPS logo" id="logo"/>

            <NavLink to="/" end className={({isActive}) => isActive ? "nav-btn active" : "nav-btn"}>
                Home
            </NavLink>

            <NavLink to="/roadmap" className="nav-btn">
                Career Roadmap
            </NavLink>

            <NavLink to="/explore" className={({isActive}) => isActive ? "nav-btn active" : "nav-btn"}>
                Explore Projects
            </NavLink>

            <NavLink to="/portfolio" className="nav-btn">
                Your Portfolio
            </NavLink>

            {isLoggedIn ? (
                <button className="nav-btn" onClick={handleLogout}>
                    Log Out
                </button>
            ) : (
                <NavLink to="/login" className={({isActive}) => isActive ? "nav-btn active" : "nav-btn"}>
                    Log In
                </NavLink>
            )}

            <button  className="nav-btn" onClick={() => setDarkMode(!darkMode)}>
                {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
            </button>
        </nav>
    );
}

export default Navbar;
