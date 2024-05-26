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

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = {};

    if (password !== confirmPassword) {
        errors.password = "Password and Confirm Password do not match";
    }
    if (!password.trim()) {
        errors.password = "Password is required";
    } else if (password.trim().length < 4) {
        errors.password = "Password must be at least 4 characters long";
    }

    if (Object.keys(errors).length > 0) {
        console.log(errors);
        return;
    }

    let formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);
    formData.append('token', token);

    let requestOption = {
        method: 'POST',
        body: formData,
        redirect: 'follow',
        credentials: "include", 
    }

    try {
        const response = await fetch('/api/v1/auth/reset-password/', requestOption);
        // const responseData = await response.text();
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
