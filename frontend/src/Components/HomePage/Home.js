import React, { useEffect, useState } from 'react';
import './Home.css';
import Sidebar from '../CommonComponents/Sidebar';
import Cards from '../CommonComponents/Cards';
import useAuthRedirect from '../CommonComponents/Hooks';

const Home = () => {
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
            const response = await fetch(`/api/v1/task/tasks/?skip=${skip}&limit=${limit}`, {
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

    const handleSearchChange = (e) => {
        setSearchQuery(e.target.value);
        setSkip(0);
        setLimit(8);
        setTotal(0);

    };

    const handleStatusFilterChange = async (e) => {
        setStatus(e.target.value);
        setSkip(0);
        setLimit(8);
        setTotal(0);

    };

    const handleCategoryFilterChange = async (e) => {
        setCategory(e.target.value);
        setSkip(0);
        setLimit(8);
        setTotal(0);

    };


    const handleDueDateFilterChange = async (e) => {
        setDueDate(e.target.value);
        setSkip(0);
        setLimit(8);
        setTotal(0);

    };

    const handleSearchSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`/api/v1/task/search/?query=${searchQuery}&skip=${skip}&limit=${limit}`, {
                method: 'GET',
                credentials: 'include',
            });
            const data = await response.json();
            setSearchResults(data.tasks);
            setSearching(true);
            setSkip(data.skip);
            setLimit(data.limit);
            setTotal(data.total);
            setPages(Math.ceil(data.total / 8));
            console.log(total, limit);

        } catch (error) {
            console.error('Error:', error);
        }
    };

    const handleFilterSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`/api/v1/task/filter/?task_status=${status}&category=${category}&due_date=${dueDate}&skip=${skip}&limit=${limit}`, {
                method: 'GET',
                credentials: 'include',
            });
            const data = await response.json();
            setFilterResults(data.tasks);
            setFiltering(true);
            setSkip(data.skip);
            setLimit(data.limit);
            setTotal(data.total);
            setPages(Math.ceil(data.total / 8));
            console.log(total, limit);

        } catch (error) {
            console.error('Error:', error);
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

    const clearFilter = () => {
        setFilterResults(null);
        setFiltering(false);
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
                    <input type="text" value={searchQuery} onChange={handleSearchChange} placeholder="Search tasks..." />
                    <button type="submit">Search</button>
                    {searching && <button type="button" onClick={clearSearch}>Clear</button>}
                </form>
            </div>
            <div className='filter-bar'>
                <form className='filter-form' onSubmit={handleFilterSubmit}>
                    <label className='filter-label' htmlFor="status">Status:</label>
                    <select className='filter-select' id="status" onChange={(e) => handleStatusFilterChange(e)}>
                        <option value="">All</option>
                        <option value="true">Completed</option>
                        <option value="false">Pending</option>
                    </select>

                    <label className='filter-label' htmlFor="category">Priority:</label>
                    <select className='filter-select' id="category" onChange={(e) => handleCategoryFilterChange(e)}>
                        <option value="">All</option>
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                    </select>

                    <label className='filter-label' htmlFor="dueDate">Due Date:</label>
                    <input className='filter-input' type="date" id="dueDate" onChange={(e) => handleDueDateFilterChange(e)} />
                    <button type="submit">Filter</button>
                    {filtering && <button type="button" onClick={clearFilter}>Clear</button>}
                </form>
            </div>

            <div className="cards-container-home">
                {searchResults ? (
                    <Cards cards={searchResults} onDelete={handleDelete} />
                ) : (
                    filterResults ? (
                        <Cards cards={filterResults} onDelete={handleDelete} />
                    ) : (
                        <Cards cards={cards} onDelete={handleDelete} />
                    )
                )}
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

export default Home;
