

async def add_fuckraid_user(user_id: int) -> bool:
    is_fuckraid = await is_fuckraid_user(user_id)
    if is_fuckraid:
        return False
    await fuckraiddb.insert_one({"user_id": user_id})
    return True


async def del_fuckraid_user(user_id: int) -> bool:
    is_fuckraid = await is_fuckraid_user(user_id)
    if not is_fuckraid:
        return False
    await fuckraiddb.delete_one({"user_id": user_id})
    return True

