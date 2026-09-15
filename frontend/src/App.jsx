import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import './App.css';
import Navbar from "./components/NavBar/Navbar";
import Footer from "./components/Footer/Footer";

import About from "./pages/About";
import Login from "./pages/Login";

function App() {
  const [darkMode, setDarkMode] = useState(false);

  return (
    <BrowserRouter>
      <div className={darkMode ? "app dark" : "app"}>
        <Navbar
          darkMode={darkMode}
          setDarkMode={setDarkMode}
        />

        <Routes>
          <Route path="/" element={<About />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login darkMode={darkMode}/>} />
        </Routes>
        <Footer />
      </div>
    </BrowserRouter>
  );
}

export default App
