def map_model_to_user_with_credentials(user_model) -> 'UserWithCredentials':
    return UserWithCredentials(
        id=user_model.id,
        student_number=user_model.student_number,
        encrypted_password=user_model.encrypted_password,
    )