import React, { useState } from 'react';
import './Sidebar.css';
import Swal from 'sweetalert2';
import { Link, useNavigate } from 'react-router-dom';

import { useCookies } from 'react-cookie';
import gif_img from '../../assets/images/todo_logo_small.png';

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
            <button className="toggle-btn-menu" onClick={toggleSidebar}>
                <div><img src={gif_img} alt='login' height="54px" width="54px" className='logo-small-imageClass' /></div>
                <span className={`arrow-icon ${isOpen ? 'open' : ''}`}>
                    {isOpen ? <i className="fas fa-arrow-left"></i> : <i className="fas fa-arrow-right"></i>}
                </span>
            </button>
            <hr />
            <nav>
                <ul>
                    <li>
                        <Link to="/home" className="menu-link">
                            <span className="icon">
                                <i className="fas fa-home"></i>
                            </span>
                            <span className={`menu ${isOpen ? 'open' : ''}`}>Home</span>
                        </Link>
                    </li>
                    <hr className='hr' />
                    <li>
                        <Link to="/create-task" className="menu-link">
                            <span className="icon">
                                <i className="fas fa-plus"></i>
                            </span>
                            <span className={`menu ${isOpen ? 'open' : ''}`}>Add New</span>
                        </Link>
                    </li>
                    <hr className='hr' />
                    <li>
                        <Link to="/profile" className="menu-link">
                            <span className="icon">
                                <i className="fas fa-user"></i>
                            </span>
                            <span className={`menu ${isOpen ? 'open' : ''}`}>Profile</span>
                        </Link>
                    </li>
                    {isAdmin.is_admin === 1 && (
                        <>
                            <hr className='hr' />
                            <li>
                                <Link to="/delete-requests" className="menu-link">
                                    <span className="icon">
                                        <i className="fas fa-trash"></i>
                                    </span>
                                    <span className={`menu ${isOpen ? 'open' : ''}`}>Delete Request</span>
                                </Link>
                            </li>
                            
                        </>
                    )}
                    <hr className='hr' />
                    {id.id ? (
                        <div className="auth_btn">
                            <hr className='hr' />
                            <hr className='hr' />
                            <hr className='hr' />
                            <li>
                                <Link onClick={logoutSubmitted} className="menu-link">
                                    <span className="icon">
                                        <i className="fas fa-sign-out-alt"></i>
                                    </span>
                                    <span className={`menu ${isOpen ? 'open' : ''}`}>Log Out</span>
                                </Link>
                            </li>
                            <hr className='hr' />
                            <hr className='hr' />
                            <hr className='hr' />
                        </div>
                    ) : (
                        <div className="auth_btn">
                            <hr className='hr' />
                            <hr className='hr' />
                            <hr className='hr' />
                            <li>
                                <Link to="/login" className="menu-link">
                                    <span className="icon">
                                        <i className="fas fa-user"></i>
                                    </span>
                                    <span className={`menu ${isOpen ? 'open' : ''}`}>Login</span>
                                </Link>
                            </li>
                            <hr className='hr' />
                            <hr className='hr' />
                            <hr className='hr' />
                        </div>
                    )}
                </ul>
            </nav>
        </aside>
    );
}

export default Sidebar;
