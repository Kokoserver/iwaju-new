import type { PageServerLoad } from './$types';
import { get_addressList } from '$root/lib/utils/page/address';

export const load: PageServerLoad = async ({ fetch }) => {
	return {
		addressList: get_addressList(fetch)
	};
};
