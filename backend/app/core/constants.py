class SystemMessages:
    # Error messages
    ERROR_CREATE_USER = "Failed to create user."
    ERROR_CREATE_USER_DETAIL = "Failed to create user."
    ERROR_RESET_EMAIL = "Failed to send reset email."
    ERROR_RESET_EMAIL_DETAIL = "Failed to send reset email."
    ERROR_UPDATE_USER = "Failed to update user."
    ERROR_UPDATE_USER_DETAIL = "Failed to update user."
    ERROR_LOGIN = "Failed to log in."
    ERROR_LOGIN_DETAIL = "Failed to log in."
    ERROR_USER_NOT_FOUND = "User not found."
    ERROR_USER_NOT_FOUND_DETAIL = "User not found."
    ERROR_VERIFICATION_FAILED = "Verification failed."
    ERROR_VERIFICATION_FAILED_DETAIL = "Verification failed."
    ERROR_RESET_TOKEN = "Invalid reset token."
    ERROR_RESET_TOKEN_DETAIL = "Invalid reset token."
    ERROR_USER_NOT_FOUND_ID = "User not found with id"
    ERROR_PERMISSION_DENIED = "Permission denied."
    ERROR_INTERNAL_SERVER = "Internal Server Error"
    ERROR_INVALID_CREDENTIALS = "Invalid Credentials"
    ERROR_USER_NOT_ACTIVE = "User is not active"
    ERROR_FAILED_TO_SEND_RESET_EMAIL = "Failed to send reset email:"
    ERROR_FAILED_TO_RESET_PASSWORD = "Failed to reset password:"
    ERROR_INVALID_RESET_TOKEN = "Invalid reset Token"
    ERROR_FAILED_TO_CHANGE_PASSWORD = "Failed to change password:"
    ERROR_FAILED_TO_CREATE_TASK = "Failed to create task:"
    ERROR_FAILED_TO_FETCH_TASKS = "Failed to fetch tasks:"
    ERROR_FAILED_TO_SEARCH_TASKS = "Failed to search tasks:"
    ERROR_FAILED_TO_FILTER_TASKS = "Failed to filter tasks:"
    ERROR_FAILED_TO_FETCH_TASK = "Failed to fetch task:"
    ERROR_FAILED_TO_UPDATE_TASK = "Failed to update task:"
    ERROR_FAILED_TO_UPDATE_TASK_STATUS = "Failed to update task status:"
    ERROR_FAILED_TO_DELETE_TASK = "Failed to delete task:"
    ERROR_FAILED_TO_REQUEST_DELETE_TASK = "Failed to request delete task:"

    # Success messages
    SUCCESS_USER_CREATED = "User created successfully."
    SUCCESS_PASSWORD_RESET_EMAIL_SENT = "Password reset email sent successfully."
    SUCCESS_PASSWORD_RESET = "Password reset successful."
    SUCCESS_USER_UPDATED = "User updated successfully."
    SUCCESS_USER_LOGGED_IN = "User logged in successfully."
    SUCCESS_USER_LOGGED_OUT = "Logged out successfully."
    SUCCESS_USER_FETCHED = "User fetched successfully."
    SUCCESS_LOGGED_OUT = "Logged out successfully"
    SUCCESS_RESET_EMAIL_SENT = "Password reset email sent successfully"
    SUCCESS_PASSWORD_RESETFUL = "Password reset successful for email:"
    SUCCESS_PASSWORD_CHANGED = "Password changed successfully for user_id:"

    # Log messages
    LOG_ATTEMPT_UPDATE_USER = "Attempting to update user with id:"
    LOG_USER_DOES_NOT_EXIST = "User with id {id} does not exist"
    LOG_USER_UPDATED_SUCCESSFULLY = "User with id: {id} updated successfully."
    LOG_ATTEMPT_LOGIN = "Attempting login for username:"
    LOG_USER_NOT_FOUND = "User not found for username:"
    LOG_USER_FOUND = "User found:"
    LOG_INVALID_PASSWORD = "Invalid password for username:"
    LOG_INACTIVE_USER_LOGIN = "Inactive user attempted login with username:"
    LOG_USER_LOGGED_IN_SUCCESSFULLY = "User logged in successfully"
    LOG_USER_LOGIN_FAILED = "Failed to log in:"
    LOG_LOGGING_OUT_USER = "Logging out user"
    LOG_SENDING_RESET_EMAIL = "Attempting to send password reset email to:"
    LOG_USER_NOT_FOUND_FOR_EMAIL = "User not found for email:"
    LOG_CHANGE_PASSWORD_ATTEMPT = "Attempting to change password for user_id:"
    LOG_RESET_PASSWORD_ATTEMPT = "Attempting to reset password for email:"
    LOG_TASK_CREATED_SUCCESSFULLY = "Task created successfully with id:"
    LOG_ATTEMPT_FETCH_TASKS = (
        "Fetching tasks with query: {query}, skip: {skip}, limit: {limit}"
    )
    LOG_FETCHED_TASKS = "Fetched tasks"
    LOG_FETCH_DELETE_REQUEST_TASKS = (
        "Fetching tasks with delete request True, skip: {skip}, limit: {limit}"
    )
    LOG_FETCH_SEARCH_TASKS = (
        "Searching tasks with query: {query}, skip: {skip}, limit: {limit}"
    )
    LOG_FETCH_FILTER_TASKS = "Filter tasks endpoint called with parameters: task_status={task_status}, category={category}, due_date={due_date}, skip={skip}, limit={limit}, user_id={user_id}, user_role={user_role}"
    LOG_FETCH_TOTAL_TASKS = "Total tasks: {total}"
    LOG_FETCH_TASK_BY_ID = "Fetching task with id: {task_id}"
    LOG_FETCH_TASK_SUCCESS = "Task with id {task_id} fetched successfully"
    LOG_UPDATE_TASK_BY_ID = "Updating task with id: {task_id}"
    LOG_TASK_UPDATED_SUCCESSFULLY = "Task with id {task_id} updated successfully"
    LOG_UPDATE_TASK_STATUS = "Updating status of task with id: {task_id} to {status}"
    LOG_TASK_STATUS_UPDATED_SUCCESSFULLY = (
        "Status of task with id {task_id} updated successfully"
    )
    LOG_HTTP_EXCEPTION = "HTTP Exception occurred"
    LOG_DELETING_TASK = "Deleting task with id: {task_id}"
    LOG_TASK_DELETE_REQUEST = "Deleting task with id: {task_id}"
    LOG_TASK_DELETE_REQUEST_SUCCESS = "Task with id {task_id} delete requested successfully"

    # Warning messages
    WARNING_INVALID_RESET_TOKEN = "Invalid reset token for email:"
    WARNING_USER_NOT_FOUND_FOR_EMAIL = "User not found for email:"
    WARNING_TASK_NOT_FOUND = "Task with id {task_id} not found"
    
    
    #Roles
    ADMIN = "admin"
    USER = "user"


