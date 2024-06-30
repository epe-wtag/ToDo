import React, { useEffect, useState } from 'react';
import './DeleteRequest.css';
import Sidebar from '../CommonComponents/Sidebar';
import Cards from '../CommonComponents/Cards';
import useAuthRedirect from '../CommonComponents/Hooks';

const DeleteRequest = () => {
    useAuthRedirect();
    const [cards, setAllCards] = useState([]);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(0);
    const [skip, setSkip] = useState(0);
    const [limit, setLimit] = useState(8);
    const [reload, setReload] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);
    const [searching, setSearching] = useState(false);

    useEffect(() => {
        if (!searching) {
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
            console.log("Fetched data:", data);
            if (data.tasks) {
                setAllCards(data.tasks);
                setTotal(data.total);
                setPages(data.total);
            } else {
                console.error("Unexpected data format:", data);
            }
        } catch (error) {
            console.error('Error fetching tasks:', error);
        }
    };

    const handleDelete = () => {
        setReload(!reload);
    };

    const handleNext = () => {
        const newSkip = skip + limit;
        setSkip(Math.min(newSkip, total - limit));
    };

    const handlePrevious = () => {
        const newSkip = skip - limit;
        setSkip(Math.max(newSkip, 0));
    };

    const handleSearchChange = (e) => {
        setSearchQuery(e.target.value);
    };

    const handleSearchSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`/api/v1/task/search-delete-requested-tasks/?query=${searchQuery}&skip=${skip}&limit=${limit}`, {
                method: 'GET',
                credentials: 'include',
            });
            const data = await response.json();
            console.log("Search results:", data);
            setSearchResults(data.tasks);
            setSearching(true);
            setTotal(data.total);
            setPages(Math.ceil(data.total / 8));

        } catch (error) {
            console.error('Error searching tasks:', error);
        }
    };

    const clearSearch = () => {
        setSearchQuery('');
        setSearchResults(null);
        setSearching(false);
        setSkip(0);
        setLimit(8);
        setTotal(9);
        setReload(!reload);
    };

    return (
        <>
            <Sidebar />
            <div className="search-bar">
                <form onSubmit={handleSearchSubmit}>
                    <input type="text" value={searchQuery} onChange={handleSearchChange} placeholder="Search tasks by user" />
                    <button type="submit">Search</button>
                    {searching && <button type="button" onClick={clearSearch}>Clear</button>}
                </form>
            </div>
            <h2 className='h2-delete'></h2>

            

            <div className="cards-container-delete-page">
                <Cards cards={searchResults || cards} onDelete={handleDelete} />
            </div>
            {pages > limit && (
                <div className="pagination-controls">
                    <button onClick={handlePrevious} disabled={skip === 0}>
                        Previous
                    </button>
                    <span>
                        Page {skip / limit + 1} of {Math.ceil(total / limit)}
                    </span>
                    <button onClick={handleNext} disabled={skip + limit >= total}>
                        Next
                    </button>
                </div>
            )}
        </>
    );
};

export default DeleteRequest;
