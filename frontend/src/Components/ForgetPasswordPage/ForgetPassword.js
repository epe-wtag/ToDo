import React, { useState } from 'react';
import './ForgetPassword.css';
import { Link, useNavigate } from 'react-router-dom'; 
import Swal from 'sweetalert2'; 

const ForgetPassword = () => {
  const [email, setEmail] = useState('');

  let navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = {};

    if (!email.trim()) {
        errors.email = "Email Address is required";
    } else if (!/\S+@\S+\.\S+/.test(email)) {
        errors.email = "Invalid email format";
    }
    if (Object.keys(errors).length > 0) {
        console.log(errors);
        return;
    }

    let formData = new FormData();
        formData.append('email', email);

    let requestOption = {
        method: 'POST',
        body: formData,
        redirect: 'follow',
        credentials: "include", 
    }

    try {
        const response = await fetch('/api/v1/auth/forget-password', requestOption);
        // const responseData = await response.text();
        // const cookie = response.headers.get('Set-Cookie');
        // const jsonResponse = JSON.parse(responseData);
        console.log('success !!!');
        
        Swal.fire({
            icon: 'success',
            title: 'Reset link has been sent to this email!',
            showConfirmButton: false,
            timer: 1500
        });
        navigate('/login');
    } catch (error) {
        console.log('Error: ', error);
    }

  };

  return (
    <div className="forget-password-container">
      <h2>Forgot Your Password?</h2>
      <form onSubmit={handleSubmit} className="forget-password-form">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          required
        />
        <button type="submit">Find Me</button>
      </form>
    </div>
  );
};

export default ForgetPassword;
