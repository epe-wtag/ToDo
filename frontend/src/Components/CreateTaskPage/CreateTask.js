import React, { useState } from 'react';
import './CreateTask.css';
import Sidebar from '../CommonComponents/Sidebar';
import { useNavigate } from 'react-router-dom'; 
import Swal from 'sweetalert2';

const CreateTask = () => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [dueDate, setDueDate] = useState('');
    const [category, setCategory] = useState('low');

    let navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        const formData = new FormData();
        formData.append('title', title);
        formData.append('description', description);
        formData.append('due_date', dueDate);
        formData.append('category', category);

        try {

            let requestOption = {
                method: 'POST',
                body: formData,
                redirect: 'follow',
                credentials: "include",
            }


            const response = await fetch('/api/v1/task/tasks/', requestOption);
            if (response.ok) {
                const data = await response.json();
                Swal.fire({
                    icon: 'success',
                    title: 'Task Created Successfully!',
                    text: `Task ID: ${data.id}`,
                    showConfirmButton: false,
                    timer: 1500
                });
                setTitle('');
                setDescription('');
                setDueDate('');
                setCategory('low');
                navigate('/home');
            } else {
                console.error('Error creating task:', response.statusText);
            }
        } catch (error) {
            console.error('Error creating task:', error);
        }
    };

    return (
        <>
            <Sidebar />
            <div className="home-container-wrap">
                <div className="home-container">
                    <h2 className="h2-task">Create a New Task</h2>
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="title">Title:</label>
                            <input
                                type="text"
                                id="title"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="description">Description:</label>
                            <textarea
                                rows={10}
                                id="description"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                required
                            ></textarea>
                        </div>

                        <div className="form-group">
                            <label htmlFor="dueDate">Due Date:</label>
                            <input
                                type="date"
                                id="dueDate"
                                value={dueDate}
                                onChange={(e) => setDueDate(e.target.value)}
                            />
                        </div>

                        <div className="form-group">
                            <label className="label-cat" htmlFor="category">Category:</label>
                            <select
                                className="select-cat"
                                id="category"
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                            </select>
                        </div>
                        <button type="submit">Create Task</button>
                    </form>
                </div>
            </div>
        </>
    );
};

export default CreateTask;
