import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './ResetPassword.css';
import Swal from 'sweetalert2'; 

const ResetPassword = () => {
  const { email, token } = useParams();

  console.log(token);

  let navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');


  const isValidPassword = (password) => {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    return password.length >= minLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;
};

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = {};

    if (!isValidPassword(password)) {
      Swal.fire({
          icon: 'error',
          title: 'Invalid Password',
          text: 'Password must be at least 8 characters long and include an uppercase letter, a lowercase letter, a number, and a special character',
      });
      return;
  }

    if (password !== confirmPassword) {
      Swal.fire({
        icon: 'error',
        title: 'Invalid Password',
        text: 'Password and Confirm Password do not match',
    });
    return;
    }
    if (!password.trim()) {
        errors.password = "Password is required";
    } else if (password.trim().length < 4) {
      Swal.fire({
        icon: 'error',
        title: 'Invalid Password',
        text: 'Password must be at least 4 characters long',
    });
    return;
    }

    if (Object.keys(errors).length > 0) {
        console.log(errors);
        return;
    }

    const data = {
      email: email,
      password: password,
      token: token
  };

    let requestOption = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
        redirect: 'follow',
        credentials: "include", 
    }

    try {
        const response = await fetch('/api/v1/auth/reset-password/', requestOption);
        
        console.log('success !!!');
        Swal.fire({
            icon: 'success',
            title: 'successfully reset the password!',
            showConfirmButton: false,
            timer: 1500
        });
        navigate('/login');
    } catch (error) {
        console.log('Error: ', error);
    }

    
  };

  return (
    <div className="reset-container">
      <h2>Reset Password</h2>
      <form onSubmit={handleSubmit} className="reset-form">
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="New Password"
          required
        />
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Confirm New Password"
          required
        />
        <button type="submit">Reset Password</button>
      </form>
    </div>
  );
};

export default ResetPassword;
