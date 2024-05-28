import React, { useEffect, useState } from 'react';
import './DeleteRequest.css';
import Sidebar from '../CommonComponents/Sidebar';
import Cards from '../CommonComponents/Cards';
import useAuthRedirect from '../CommonComponents/Hooks';

const DeleteRequest = () => {
    useAuthRedirect();
    const [cards, setAllCards] = useState([]);
    const [total, setTotal] = useState(9);
    const [pages, setPages] = useState(0);
    const [skip, setSkip] = useState(0);
    const [limit, setLimit] = useState(8);
    const [reload, setReload] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);
    const [filterResults, setFilterResults] = useState(null);
    const [searching, setSearching] = useState(false);
    const [filtering, setFiltering] = useState(false);
    const [status, setStatus] = useState('');
    const [category, setCategory] = useState('');
    const [dueDate, setDueDate] = useState('');

    useEffect(() => {
        if (!searching && !filtering) {
            fetchTasks();
        }
    }, [skip, limit, reload, searching]);

    const fetchTasks = async () => {
        try {
            const response = await fetch(`/api/v1/task/delete-requested-tasks/?skip=${skip}&limit=${limit}`, {
                method: 'GET',
                credentials: 'include',
            });
            const data = await response.json();
            setAllCards(data.tasks);
            console.log(data.tasks);
            if (data.total >= 0) {
                setTotal(data.total);
                setPages(data.total);
            };
        } catch (error) {
            console.error('Error:', error);
        }
    };

    const handleDelete = () => {
        setReload(!reload);
    };



    const handleNext = () => {
        const newSkip = skip + limit;
        if (newSkip < total) {
            setSkip(newSkip);
        } else {
            setSkip(Math.max(0, total - limit));
        }

    };

    const handlePrevious = () => {
        const newSkip = skip - limit;
        if (newSkip >= 0) {
            setSkip(newSkip);
        } else {
            setSkip(0);
        }
    };


    return (
        <>
            <Sidebar />
            <h2 className='h2-delete'>Delete Requests</h2>

            <div className="cards-container-delete-page">
                <Cards cards={cards} onDelete={handleDelete} />
            </div>
            {pages > 8 && (
                <div className="pagination-controls">
                    <button onClick={handlePrevious} disabled={skip === 0}>
                        Previous
                    </button>
                    <span>
                        Page {total && limit ? Math.ceil(skip / limit) + 1 : 1} of {total && limit ? Math.ceil(total / limit) : 1}
                    </span>
                    <button onClick={handleNext} disabled={skip + limit >= total}>
                        Next
                    </button>
                </div>)}
        </>
    );
};

export default DeleteRequest;
