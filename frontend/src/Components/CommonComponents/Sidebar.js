import React, { useState } from 'react';
import './Sidebar.css';
import Swal from 'sweetalert2';
import { Link, useNavigate } from 'react-router-dom';

import { useCookies } from 'react-cookie';

const Sidebar = () => {

    const [id, , removeId] = useCookies(['id']);
    const [isAdmin, , removeIsAdmin] = useCookies(['is_admin']);
    const [isOpen, setIsOpen] = useState(false);

    const navigate = useNavigate();

    const toggleSidebar = () => {
        setIsOpen(!isOpen); 
    }



    const logoutSubmitted = async (e) => {
        e.preventDefault();
        

        let formData = new FormData();

        let requestOption = {
            method: 'POST',
            body: formData,
            redirect: 'follow',
            credentials: "include",
        }

        try {
            const response = await fetch('/api/v1/auth/logout/', requestOption);
            Swal.fire({
                icon: 'success',
                title: 'Log out successfull !!!',
                showConfirmButton: false,
                timer: 1500
            });
            removeId('id');
            removeIsAdmin('is_admin')
            navigate('/');
        } catch (error) {
            console.log('Error: ', error);
        }
    };

    return (
        <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
            <button className="toggle-btn" onClick={toggleSidebar}>
            <p className="logo-cover-small">
                        <p className="logo-small">
                            <Link to="/">
                                <h3>🛠️ To-Do 🛠️</h3>
                                                        
                            </Link>
                        </p>
                    </p>
             <span>▽</span>
            </button>
            <nav>
                <ul>
                    <p className="logo-cover">
                        <p className="logo">
                            <Link to="/home">
                                <h3>🛠️ To-Do 🛠️</h3>
                                                        
                            </Link>
                        </p>
                    </p>
                <hr />
                <hr />
                    <li>
                        <Link to="/home">
                            <span className="icon">
                                <i className="fas fa-home"></i>
                            </span>
                            || &nbsp; Home
                        
                        </Link>
                    </li>
                    <hr />
                    {isAdmin.is_admin === 1 && (
                    <li>
                        <Link to="/create-task">
                            <span className="icon">
                                <i className="fas fa-plus"></i>
                            </span>
                            || &nbsp; Add a Task
                           
                        </Link>
                    </li>
                    )}
                    <hr />
                    <li>
                        <Link to="/profile">
                            <span className="icon">
                                <i className="fas fa-user"></i>
                            </span>
                            || &nbsp; My Profile
                            
                        </Link>
                    </li>
                    <hr />
                    <li>
                        <Link to="/about">
                            <span className="icon">
                                <i className="fas fa-info-circle"></i>
                            </span>
                            || &nbsp; About
                          
                        </Link>
                    </li>
                    <hr />
                    <li>
                        <Link to="/contact">
                            <span className="icon">
                                <i className="fas fa-envelope"></i>
                            </span>
                            || &nbsp; Contact
                          
                        </Link>
                    </li>
                    <hr />
                    <hr />
                    
                    {id.id ? (
                        <div className="auth_btn">
                        <hr />
                        <hr />
                        <hr />
                        <li>
                            <span className="icon">
                                <i className="fas fa-sign-out-alt"></i>
                            </span>
                            <Link onClick={logoutSubmitted}>Log Out</Link>
                        </li>
                            <hr />
                            <hr />
                            <hr />
                        </div>
                    ) : (
                        <div className="auth_btn">
                            <hr />
                            <hr />
                            <hr />
                            <li>
                                <Link to="/login">
                                    <span className="icon">
                                        <i className="fas fa-user"></i>
                                    </span>
                                    Log In
                                </Link>
                            </li>
                            <hr />
                            <hr />
                            <hr />
                        </div>
                    )}
                </ul>
            </nav>
        </aside>
    );
}

export default Sidebar;
