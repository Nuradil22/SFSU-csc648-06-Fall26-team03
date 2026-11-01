
import { useEffect, useState } from 'react';
import { useLocation, NavLink, useNavigate } from 'react-router-dom';
import './Navbar.css';
import logo from '../../assets/light-logo-p.png';
import darkLogo from '../../assets/dark-logo-P.png';
import { getToken, logout } from '../../lib/api';

function Navbar({ darkMode, setDarkMode }) {
    const navigate = useNavigate();
    const location = useLocation();

    const [isLoggedIn, setIsLoggedIn] = useState(
        Boolean(getToken())
    );

    // Recheck login status whenever the route changes.
    useEffect(() => {
        setIsLoggedIn(Boolean(getToken()));
    }, [location.pathname]);

    async function handleLogout() {
        await logout().catch(() => {});
        setIsLoggedIn(false);
        navigate('/');
    }

    return (
        <nav className="navbar">
            <img
                src={darkMode ? darkLogo : logo}
                alt="CareerGPS logo"
                id="logo"
            />

            {isLoggedIn ? (
                <NavLink
                    to="/account/dashboard"
                    className={({ isActive }) =>
                        isActive ? "nav-btn active" : "nav-btn"
                    }
                >
                    Dashboard
                </NavLink>
            ) : (
                <NavLink
                    to="/"
                    end
                    className={({ isActive }) =>
                        isActive ? "nav-btn active" : "nav-btn"
                    }
                >
                    Home
                </NavLink>
            )}

            <NavLink to="/roadmap" className="nav-btn">
                Career Roadmap
            </NavLink>

            <NavLink
                to="/explore"
                className={({ isActive }) =>
                    isActive ? "nav-btn active" : "nav-btn"
                }
            >
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
                <NavLink
                    to="/login"
                    className={({ isActive }) =>
                        isActive ? "nav-btn active" : "nav-btn"
                    }
                >
                    Log In
                </NavLink>
            )}

            <button
                className="nav-btn"
                onClick={() => setDarkMode(!darkMode)}
            >
                {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
            </button>
        </nav>
    );
}

export default Navbar;
