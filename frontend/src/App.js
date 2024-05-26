import { BrowserRouter, Route, Routes } from 'react-router-dom';

import ChangePassword from './Components/ChangePasswordPage/ChangePassword';
import ForgetPassword from './Components/ForgetPasswordPage/ForgetPassword';
import Home from './Components/HomePage/Home';
import Landing from './Components/LandingPage/Landing';
import Login from './Components/LoginPage/Login';
import Profile from './Components/ProfilePage/Profile';
import ResetPassword from './Components/ResetPasswordPage/ResetPassword';
import Signup from './Components/SignupPage/Signup';

import './App.css';


function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/sign-up" element={<Signup />} />
          <Route path="/login" element={<Login />} />
          <Route path="/home" element={<Home />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/forget-password" element={<ForgetPassword />} />
          <Route path="/reset-password/:email/:token" element={<ResetPassword />} />
          <Route path="/change-password" element={<ChangePassword />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
