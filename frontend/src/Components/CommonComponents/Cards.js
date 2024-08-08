import React, { useState, useEffect } from 'react';
import { useCookies } from 'react-cookie';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Link } from 'react-router-dom';
import Swal from 'sweetalert2';
import incomplete from '../../assets/images/Incomplete.png';
import complete from '../../assets/images/completed.png';
import pending from '../../assets/images/pending.png';
import './Cards.css';

const Cards = ({ cards, onDelete }) => {
    const [id, ,] = useCookies(['id']);
    const [isAdmin, ,] = useCookies(['is_admin']);
    const [showModal, setShowModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [selectedCard, setSelectedCard] = useState(null);
    const [editedTitle, setEditedTitle] = useState('');
    const [editedDescription, setEditedDescription] = useState('');
    const [editedDueDate, setEditedDueDate] = useState('');
    const [category, setCategory] = useState('low');
    const [userData, setUserData] = useState({});

    useEffect(() => {
        const fetchUserData = async () => {
            const uniqueOwnerIds = [...new Set(cards.map(card => card.owner_id))];
            const userRequests = uniqueOwnerIds.map(ownerId =>
                fetch(`/api/v1/user/user/${ownerId}`).then(res => res.json())
            );

            try {
                const users = await Promise.all(userRequests);
                const usersMap = {};
                users.forEach(user => {
                    usersMap[user.id] = user;
                });
                setUserData(usersMap);
            } catch (error) {
                console.error('Failed to fetch user data:', error);
            }
        };

        fetchUserData();
    }, [cards]);

    const toggleModal = (task) => {
        setSelectedCard(task);
        setShowModal(!showModal);
        setShowEditModal(false);

        setEditedTitle(task.title);
        setEditedDescription(task.description);
        setEditedDueDate(task.due_date ? new Date(task.due_date).toISOString().split('T')[0] : '');
        setCategory(task.category);
    };

    const toggleEditModal = () => {
        setShowEditModal(!showEditModal);
        setShowModal(false);
    };

    const formatDate = (dateString) => new Date(dateString).toLocaleDateString();

    const deleteTask = async (taskId) => {
        Swal.fire({
            title: 'Are you sure?',
            text: 'Once deleted, you will not be able to recover this task!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, delete it!',
        }).then(async (result) => {
            if (result.isConfirmed) {
                let requestOption = {
                    method: 'DELETE',
                    redirect: 'follow',
                    credentials: 'include',
                };
                try {
                    const response = await fetch(`/api/v1/task/tasks/${taskId}`, requestOption);
                    if (response.ok) {
                        setShowModal(false);
                        onDelete();
                        console.log('Successfully Deleted');
                        Swal.fire('Deleted!', 'Your task has been deleted.', 'success');
                    } else {
                        console.error('Failed to delete the task:', response.statusText);
                    }
                } catch (error) {
                    console.error('Error deleting the task:', error);
                }
            }
        });
    };

    const deleteRequestTask = async (taskId) => {
        console.log(selectedCard.title);
        let requestOption = {
            method: 'PUT',
            redirect: 'follow',
            credentials: "include",
        }
        try {
            const response = await fetch(`/api/v1/task/task-delete-request/${taskId}`, requestOption);
            if (response.ok) {
                setShowModal(false);
                onDelete();
                console.log("Successfully Deleted");
            } else {
                console.error('Failed to delete the task:', response.statusText);
            }
        } catch (error) {
            console.error('Error deleting the task:', error);
        }
    };

    const editTask = async (e) => {
        e.preventDefault();

        const data = {
            title: editedTitle,
            description: editedDescription,
            due_date: editedDueDate,
            category: category,
            owner_id: selectedCard.owner_id
          };

        try {
            const response = await fetch(`/api/v1/task/tasks/${selectedCard.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                  },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                setShowEditModal(false);
                onDelete();
                toast.success('Task updated successfully');
            } else {
                const errorData = await response.json();
                switch (response.status) {
                    case 422:
                        Swal.fire({
                            icon: 'error',
                            title: 'Validation Error',
                            text: errorData.detail.includes('due_date') ? 
                                'Due date must be greater than the current date.' : 
                                'Invalid data. Please check your input and try again.',
                        });
                        break;
                    case 404:
                        Swal.fire({
                            icon: 'error',
                            title: 'Not Found',
                            text: 'Task not found.',
                        });
                        break;
                    case 401:
                        Swal.fire({
                            icon: 'error',
                            title: 'Unauthorized',
                            text: 'You do not have permission to update this resource.',
                        });
                        break;
                    case 304:
                        Swal.fire({
                            icon: 'error',
                            title: 'Not Modified',
                            text: 'Task could not be updated. Please try again later.',
                        });
                        break;
                    default:
                        Swal.fire({
                            icon: 'error',
                            title: 'Oops...',
                            text: 'Failed to edit the task. Please try again later.',
                        });
                        break;
                }
                console.error('Failed to edit the task:', response.statusText);
            }
        } catch (error) {
            console.error('Error editing the task:', error);
            Swal.fire({
                icon: 'error',
                title: 'Oops...',
                text: 'Failed to edit the task. Please try again later.',
            });
        }
    };

    const changeStatus = async (e) => {
        e.preventDefault();

        const formData = new FormData();
        formData.append('status', !selectedCard.status);

        try {
            const response = await fetch(`/api/v1/task/change-status/${selectedCard.id}`, {
                method: 'PUT',
                body: formData
            });

            if (response.ok) {
                setShowModal(false);
                onDelete();
            } else {
                console.error('Failed to edit the task:', response.statusText);
            }
        } catch (error) {
            console.error('Error editing the task:', error);
        }
    };

    const handleDateChange = (e) => {
        const selectedDate = e.target.value;
        const currentDate = new Date().toISOString().split('T')[0];

        if (selectedDate < currentDate) {
            Swal.fire({
                icon: 'error',
                title: 'Invalid Due Date',
                text: 'Due date cannot be a past date. Please select a valid date.',
            });
        } else {
            setEditedDueDate(selectedDate);
        }
    };


    if (!Array.isArray(cards)) {
        return <p className="no-products-message">No Task</p>;
    }

    const today = new Date().toISOString().split('T')[0];

    return (
        <div className="cards">
            {cards.map((task, index) => (
                <div key={index} className={`card ${task.status === true ? 'green-wrap' : 'blue-wrap'}`} onClick={() => toggleModal(task)}>
                    {task.delete_request === true && (
                        <div className="online-status-indicator"><span style={{float: 'right'}}>Requested for deletion</span></div>
                    )}

                    <div className="card-image-container">
                        {task.status === true ? (
                            <img src={complete} height="120px" width="120px" className='imageClass' alt={task.status} />
                        ) : (
                            task.due_date && new Date(task.due_date) < new Date() ? (
                                <img src={incomplete} height="120px" width="120px" className='imageClass' alt={task.status} />
                            ) : (
                                <img src={pending} height="120px" width="120px" className='imageClass' alt={task.status} />
                            )
                        )}
                    </div>
                    <h3 className="truncated-description">{task.id} - {task.title}</h3>
                    <hr />
                    <p className="truncated-description">{task.description}</p>
                    {task && task.due_date !== null && (
                        <>
                            <hr />
                            <p style={{ fontSize: '12px', color: '#7A8DFD' }}>DeadLine: {new Date(task.due_date).toLocaleDateString()}</p>
                        </>
                    )}
                    <p className="owner-name">
                        {userData[task.owner_id] && `${userData[task.owner_id].first_name} ${userData[task.owner_id].last_name}`}
                    </p>
                </div>
            ))}
            {showModal && (
                <div className="card-modal">
                    <div className={`card-modal-content ${selectedCard.status === false ? 'green-wrap' : 'blue-wrap'}`}>
                        <div className='close-div'>
                            <span className="card-close" onClick={() => setShowModal(false)}>&times;</span>
                        </div>
                        <div className='small-date'>
                            {selectedCard && selectedCard.due_date !== null && (
                                <>

                                    <p style={{ fontSize: '12px', color: '#7A8DFD', textAlign: 'left' }}>DeadLine: {formatDate(selectedCard.due_date)}</p>
                                </>
                            )}
                            <p style={{ fontSize: '12px', color: '#7A8DFD', textAlign: 'right' }}>Priority - {selectedCard.category}</p>
                        </div>

                        <hr />
                        <h3>Title:  {selectedCard.title}</h3>
                        <p className='modal-description'>Details:  {selectedCard.description}</p>
                        <hr />

                        <div className="card-buttons">
                            {(id.id === selectedCard.owner_id || isAdmin.is_admin === 1) && (
                                <Link onClick={() => toggleEditModal()} to="" className="card-edit-button"><i className="fas fa-edit"></i></Link>
                            )}
                            {isAdmin.is_admin === 1 ? (
                                <Link onClick={() => deleteTask(selectedCard.id)} className="card-delete-button"><i className="fas fa-trash"></i></Link>
                            ) : (
                                !selectedCard.delete_request && (
                                    <Link onClick={() => deleteRequestTask(selectedCard.id)} className="card-delete-button">
                                        <i className="fas fa-trash"></i>
                                    </Link>
                                )
                            )}

                            {selectedCard.status === false && new Date(selectedCard.due_date) >= new Date() && (
                                <Link onClick={(e) => changeStatus(e)} className="card-complete-button">Complete</Link>)}
                        </div>
                    </div>
                </div>
            )}

            {showEditModal && (
                <div className="card-modal-edit">
                    <div className="edit-modal">
                        <div className='close-div'>
                            <span className="card-close" onClick={() => setShowEditModal(false)}>&times;</span>
                        </div>
                        <form onSubmit={(e) => editTask(e)}>
                            <div className="edit-modal-form">
                                <label>Title:</label>
                                <input type="text" value={editedTitle} onChange={(e) => setEditedTitle(e.target.value)} />
                            </div>
                            <div className="edit-modal-form">
                                <label>Description:</label>
                                <textarea value={editedDescription} onChange={(e) => setEditedDescription(e.target.value)} />
                            </div>
                            <div className="edit-modal-form">
                                <label>Due Date:</label>
                                <input type="date" min={today} value={editedDueDate} onChange={handleDateChange} />
                            </div>
                            <div className="edit-modal-form">
                                <label className="label-cat" htmlFor="category">Priority:</label>
                                <select
                                    className="select-cat-edit"
                                    id="category"
                                    value={category}
                                    onChange={(e) => setCategory(e.target.value)}
                                >
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <button type="submit">Save Changes</button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Cards;
