import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import './App.css';
import Navbar from "./components/NavBar/Navbar";
import Footer from "./components/Footer/Footer";

import About from "./pages/About";
import Login from "./pages/Login";
import Resume from "./pages/Roadmap";
import Portfolio from "./pages/Portfolio";
import CreateProject from "./pages/CreateProject";
import AccountSetup from "./pages/AccountSetup";
import Certificates from "./pages/Certificates";
import Explore from "./pages/Explore";
import SharedPortfolio from "./pages/SharedPortfolio";

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
          <Route path="/account/setup" element={<AccountSetup darkMode={darkMode}/>} />
          <Route path="/roadmap" element={<Resume darkMode={darkMode}/>} />
          <Route path="/portfolio" element={<Portfolio darkMode={darkMode}/>} />
          <Route path="/projects/new" element={<CreateProject darkMode={darkMode}/>} />
          <Route path="/projects/:id/edit" element={<CreateProject darkMode={darkMode}/>} />
          <Route path="/explore" element={<Explore darkMode={darkMode}/>} />
          <Route path="/p/:shareToken" element={<SharedPortfolio darkMode={darkMode}/>} />
          <Route path="/resources/certificates" element={<Certificates darkMode={darkMode} />} />
        </Routes>
        <Footer />
      </div>
    </BrowserRouter>
  );
}

export default App