import { BrowserRouter, Routes, Route } from 'react-router-dom';

import Landing from './Components/LandingPage/Landing';
import Login from './Components/LoginPage/Login';
import Signup from './Components/SignupPage/Signup';

import './App.css';


function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/sign-up" element={<Signup />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
