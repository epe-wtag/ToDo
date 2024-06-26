import React, { useState } from 'react';
import './ForgetPassword.css';
import { Link, useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';

const LoaderModal = () => (
  <div className="modal">
      <div className="modal-content">
          <div className="loader"></div>
          <p className="loader_text">Loading...</p>
      </div>
  </div>
);

const ForgetPassword = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);

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

    const data = {
      email: email
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

    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/auth/forget-password', requestOption);
      if (!response.ok) {
        const errorResponse = await response.json();
        throw new Error(errorResponse.detail);
      }

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

      let errorMessage = 'Something went wrong!';
      if (error.message.includes('User not found')) {
        errorMessage = 'User not found';
      } else if (error.message.includes('Failed to send reset email')) {
        errorMessage = 'Failed to send reset email';
      } else {
        errorMessage = error.message; 
      }

      Swal.fire({
        icon: 'error',
        title: 'Operation Failed',
        text: errorMessage,
      });
    }
    finally {
      setIsLoading(false);
  }
  };

  return (
    <div className="forget-password-container">
      {isLoading && <LoaderModal />}
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
