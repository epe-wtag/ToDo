import React from 'react';
import './Landing.css';
import { Link } from 'react-router-dom';
import gif_img from '../../assets/images/todo_logo.png';

function Landing() {
  return (
    <div className="landing">
      <div className='logo-div'>
        <div><img src={gif_img} alt='login' height="154px" width="154px" className='logo-imageClass' /></div>
        <h1>TO-DO</h1>
      </div>
      <p>Start organizing your tasks today.</p>
      <div className="button-container">
        <Link className='login_button' to="/login">
           Start here
        </Link>
      </div>
    </div>
  );
}

export default Landing;
