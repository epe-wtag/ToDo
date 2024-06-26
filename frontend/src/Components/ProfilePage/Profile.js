import React, { useState, useEffect } from 'react';
import './Profile.css';
import Sidebar from '../CommonComponents/Sidebar';
import { Link } from 'react-router-dom';
import useAuthRedirect from '../CommonComponents/Hooks';

import { useCookies } from 'react-cookie';

import gif_img_female from '../../assets/images/female.gif';
import gif_img_male from '../../assets/images/male.gif';
import Swal from 'sweetalert2';

const Profile = () => {
  useAuthRedirect();



  const [credentials_, ,] = useCookies();


  const [showModal, setShowModal] = useState(false);
  const [userData, setUserData] = useState({});
  const [newUserData, setNewUserData] = useState({
    username: '',
    first_name: '',
    last_name: '',
    contact_number: '',
  });

  useEffect(() => {
    fetchUserData(credentials_.id);
  }, [credentials_.id]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewUserData({ ...newUserData, [name]: value });
  };

  const fetchUserData = async () => {
    try {
      const response = await fetch(`/api/v1/user/user/${credentials_.id}`, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",

      });
      if (response.ok) {
        const data = await response.json();
        setUserData(data);
        setNewUserData(data);
      } else {
        console.error('Error fetching Profile data:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching Profile data:', error);
    }
  };




  const handleFormSubmit = async (e) => {
    e.preventDefault();


    const data = {
      username: newUserData.username,
      first_name: newUserData.first_name,
      last_name: newUserData.last_name,
      contact_number: newUserData.contact_number
    };



    let requestOption = {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      redirect: 'follow',
      credentials: "include",
    }

    try {
      const response = await fetch(`/api/v1/user/user/${credentials_.id}`, requestOption);
      if (response.ok) {
        Swal.fire({
          icon: 'success',
          title: 'Successfully updated the user details!',
          showConfirmButton: false,
          timer: 1500
        });
      } else {
        const errorResponse = await response.json();
        let errorMessage = 'Something went wrong!';
        
        if (response.status === 404) {
          errorMessage = errorResponse.detail || 'User not found';
        } else if (response.status === 401) {
          errorMessage = errorResponse.detail || 'Unauthorized attempt';
        } else if (response.status === 500) {
          errorMessage = errorResponse.detail || 'Internal server error';
        }
  
        Swal.fire({
          icon: 'error',
          title: 'Update Failed',
          text: errorMessage,
        });
      }
    } catch (error) {
      console.error('Error updating user:', error);
      Swal.fire({
        icon: 'error',
        title: 'Update Failed',
        text: 'An unexpected error occurred.',
      });
    }


    setShowModal(false);
  };




  const formatDate = (dateString) => new Date(dateString).toLocaleDateString();

  const toggleModal = () => {
    setShowModal(!showModal);
  };

  return (
    <>
      <Sidebar />
      <div className="profile-container">
        <div className="header-container">
          <h2 className="h2-text">My Profile</h2>
          <Link onClick={toggleModal} className="edit-icon-link">
            <span className="edit-icon" role="img" aria-label="Emoji">🖊️</span>
          </Link>
        </div>
        <hr />
        <div className="profile-details">
          <div className="profile-avatar-side">
          <h2 className="h2-text">{userData.username}</h2>
            <div className="profile-avatar">
              {userData.gender === 'female' ? (
                <img src={gif_img_female} alt="Profile Avatar" />
              ) : (
                <img src={gif_img_male} alt="Profile Avatar" />
              )}
            </div>
            <div className="button-container">
              <Link className='password-button' to="/change-password">
                <span className="emoji" role="img" aria-label="Emoji">⚙️</span> Change Password
              </Link>
            </div>
          </div>
          <div className="profile-info">
            <p><strong>Name: </strong> <span>{userData.first_name} {userData.last_name}</span></p>
            <hr />
            <p><strong>Email:</strong> <span>{userData.email} </span></p>
            <hr />
            <p><strong>Contact:</strong> <span> {userData.contact_number} </span></p>
            <hr />
            <p><strong>Gender:</strong> <span>{userData.gender} </span></p>
            <hr />
            <p><strong>Joined:</strong><span> {formatDate(userData.created_at)} </span></p>
            <hr />
          </div>
        </div>
      </div>
      {showModal && (
        <div className="modal">
          <div className="modal-content">
            <span className="close" onClick={toggleModal}>&times;</span>
            <h2>Edit Profile</h2>
            <hr />

            <form onSubmit={handleFormSubmit} className="edit-profile-form">
              <div className="form-group">
                <label htmlFor="username">Username:</label>
                <input
                  type="text"
                  name="username"
                  id="username"
                  value={newUserData.username}
                  onChange={handleInputChange}
                  placeholder="Username"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="first_name">First Name:</label>
                <input
                  type="text"
                  name="first_name"
                  id="first_name"
                  value={newUserData.first_name}
                  onChange={handleInputChange}
                  placeholder="First Name"
                />
              </div>
              <div className="form-group">
                <label htmlFor="last_name">Last Name:</label>
                <input
                  type="text"
                  name="last_name"
                  id="last_name"
                  value={newUserData.last_name}
                  onChange={handleInputChange}
                  placeholder="Last Name"
                />
              </div>
              <div className="form-group">
                <label htmlFor="contact_number">Contact Number:</label>
                <input
                  type="text"
                  name="contact_number"
                  id="contact_number"
                  value={newUserData.contact_number}
                  onChange={handleInputChange}
                  placeholder="Contact Number"
                />
              </div>
              <button type="submit">Save Changes</button>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default Profile;
